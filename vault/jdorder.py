# -*- coding: utf-8 -*-
import csv
import re
from django.db import models
from task import *
from ground import *
from jdcommodity import *
from organization import *
from account import *
from decimal import Decimal

class Jdtransaction:
	pass

class Jdinvoice:
	pass

class Jdorder(models.Model):
	id = models.BigIntegerField("订单编号", primary_key=True)
	JD_ORDER_STATUS = (
		(0, "等待出库"),
		(1, "等待确认收货"),
		(2, "完成"),
		(3, "(删除)锁定"),
		(4, "(删除)等待出库"),
		(5, "(删除)等待确认收货"),
	)
	status = models.IntegerField("状态", choices=JD_ORDER_STATUS)
	task = models.OneToOneField(Task)
	fake = models.IntegerField("刷单", default=0)

	@staticmethod
	def statuses():
		r = []
		for i, v in Jdorder.JD_ORDER_STATUS:
			r.append(v)
		return r

	@staticmethod
	def str2status(s):
		for i, v in Jdorder.JD_ORDER_STATUS:
			if v == s:
				return i
		return -1

	@staticmethod
	def Import():
		def __preliminary_check():
			with open('/tmp/jd.csv', 'rb') as csvfile:
				result = True
				reader = csv.reader(csv_gb18030_2_utf8(csvfile))
				title = reader.next()
				for l in reader:
					status = get_column_value(title, l, "订单状态")
					if status not in Jdorder.statuses():
						result = False
						print "[京东订单]发现新的订单状态: {}".format(status)
						break
					jdcid = int(get_column_value(title, l, "商品ID"))
					try:
						jdc = Jdcommodity.objects.get(id=jdcid)
					except Jdcommodity.DoesNotExist as e:
						jdc = Jdcommodity(id=jdcid)
						jdc.save()
					booktime = utc_2_datetime(cst_2_utc(get_column_value(title, l, "下单时间"), "%Y-%m-%d %H:%M:%S"))
					items = Jdcommoditymap.get(jdc, booktime)
					if items == None:
						result = False
						print "{}) {}:{} 缺乏商品信息".format(booktime.astimezone(timezone.get_current_timezone()), jdc.id, get_column_value(title, l, "商品名称"))
			return result

		def __get_suffix(quantity):
			if quantity < 0:
				return "(-)"
			return "(+)"

		def __shipping_out(task, time, organization, item, quantity, repository):
			task.add_transaction("出货" + __get_suffix(quantity), time, organization, item, ("资产", "库存"), -quantity, ("支出", "出货"))
			task.add_transaction("发货" + __get_suffix(quantity), time, repository, item, ("负债", "应发"), quantity, ("支出", "发货"))

		def __deliver(task, time, item, quantity, repository):
			task.add_transaction("出库" + __get_suffix(quantity), time, repository, item, ("资产", "库存"), -quantity, ("负债", "应发"))

		def __handle_transaction(info, org, repo):
			try:
				o = Jdorder.objects.get(id=info.id)
				print "[更新订单...] {}: {}".format(info.id, info.status)
				#TODO
			except Jdorder.DoesNotExist as e:
				t = Task(desc="京东订单")
				t.save()
				f = 0
				if re.compile("朱").match(info.remark): #fake order
					f = 1
				print "[添加订单...] {}: {} | 刷单标记: {}".format(info.id, info.status, f)
				o = Jdorder(id=info.id, status=Jdorder.str2status(info.status), task=t, fake=f)
				o.save()
				if info.status in ["(删除)锁定", "(删除)等待出库", "(删除)等待确认收货"]:
					return #no transaction should be added

				#出单
				t.add_transaction("出单", info.booktime, org, Item.objects.get(name="人民币"),
					("资产", "应收账款"), info.sale, ("收入", "营业收入"))

				#出货
				if f == 1: #fake order
					__shipping_out(t, info.booktime, org, Item.objects.get(name="洗衣粉"), 1, repo)
				else:
					for i in info.invoices:
						for item in Jdcommoditymap.get(Jdcommodity.objects.get(pk=i.id), info.booktime):
							__shipping_out(t, info.booktime, org, item, i.number, repo)

				#出库
				for transaction in t.transactions.filter(desc="出货"):
					split = transaction.splits.get(account__category=3) #支出
					if info.status != "等待出库":
						__deliver(t, info.booktime, split.account.item, split.change, repo)

		def __import():
			ts = []
			with open('/tmp/jd.csv', 'rb') as csvfile:
				reader = csv.reader(csv_gb18030_2_utf8(csvfile))
				title = reader.next()
				for l in reader:
					status = get_column_value(title, l, "订单状态")
					found = False
					order_id = int(get_column_value(title, l, "订单号"))
					for t in ts:
						if t.id == order_id:
							found = True
							break
					if not found:
						t = Jdtransaction()
						t.id = order_id
						t.sale = Decimal(get_column_value(title, l, "应付金额"))
						t.remark = get_column_value(title, l, "商家备注")
						t.booktime = utc_2_datetime(cst_2_utc(get_column_value(title, l, "下单时间"), "%Y-%m-%d %H:%M:%S"))
						t.status = status
						t.invoices = []
						ts.append(t)

					invc = Jdinvoice()
					invc.id = int(get_column_value(title, l, "商品ID"))
					invc.name = get_column_value(title, l, "商品名称")
					invc.number = int(get_column_value(title, l, "订购数量"))
					invc.status = get_column_value(title, l, "订单状态")
					invc.depository = get_column_value(title, l, "仓库名称")
					t.invoices.append(invc)

				org = Organization.objects.get(name="为绿厨具专营店")
				repo = Organization.objects.get(name="孤山仓")
				for t in ts:
					__handle_transaction(t, org, repo)

		if __preliminary_check():
			__import()
		else:
			print "请完善相关信息后重试!!!"
