# -*- coding: utf-8 -*-
import csv
import re
from django.db import models
from task import *
from ground import *
from jdcommodity import *
from organization import *
from account import *
from util import *
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
		(6, "锁定"),
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
		#为订单中的每一条出货记录添加相应的Transaction(s)
		def __add_shipping_transactions(task, organization, repository, info):
			for i, v in enumerate(info.invoices):
				for c in Jdcommoditymap.get(Jdcommodity.objects.get(pk=v.id), info.booktime):
					if info.status == "等待出库":
						Transaction.add(task, "{}.{}.出货".format(i+1, c.name), info.booktime, organization, c.item_ptr,
							("负债", "应发", repository), v.number, ("支出", "出货", repository))
					else:
						Transaction.add(task, "{}.{}.出货".format(i+1, c.name), info.booktime, organization, c.item_ptr,
							("资产", "完好", repository), -v.number, ("支出", "出货", repository))

		#增加一条刷单Transaction
		def __add_fake_transaction(task, organization, repository, info):
					c = Commodity.objects.get(name="洗衣粉")
					Transaction.add(task, "0.{}.出货".format(c.name), info.booktime, organization, c.item_ptr,
						("资产", "完好", repository), -1, ("支出", "出货", repository))

		def __add_commodity_transaction(task, organization, repository, info, fake):
			if fake:
				__add_fake_transaction(task, organization, repository, info)
			else:
				__add_shipping_transactions(task, organization, repository, info)

		def __handle_transaction(info, org, repo):
			if info.status == "锁定":
				return

			f = 0
			if re.compile("朱").match(info.remark): #fake order
				f = 1
			try:
				o = Jdorder.objects.get(id=info.id)
				if info.status in ["(删除)锁定", "(删除)等待出库", "(删除)等待确认收货"]:
					for t in o.task.transactions.all():
						t.delete()
					return

				if o.fake != f: #刷单状态变更
					#delete obsolete transactions and re-add
					for i in range(len(info.invoices)+1):
						s = "{}.".format(i)
						for t in o.task.transactions.filter(desc__startswith=s):
							t.delete()
					__add_commodity_transaction(o.task, org, repo, info, f)
				elif not f: #正常订单状态迁移
					for i in range(len(info.invoices)):
						s = "{}.".format(i+1)
						for t in o.task.transactions.filter(desc__startswith=s):
							s = t.splits.exclude(account__category=3)[0]
							if s.account.category == 1 and info.status != "等待出库":
								a = s.account
								s.account = Account.get(a.organization, a.item, "资产", "完好", a.repository)
								s.change = -s.change
								s.save()

				o.status = Jdorder.str2status(info.status)
				o.fake = f
				o.save()
			except Jdorder.DoesNotExist as e:
				t = Task(desc="京东订单")
				t.save()
				o = Jdorder(id=info.id, status=Jdorder.str2status(info.status), task=t, fake=f)
				o.save()
				if info.status in ["(删除)锁定", "(删除)等待出库", "(删除)等待确认收货"]:
					return #no transaction should be added
				Transaction.add(t, "出单", info.booktime, org, Money.objects.get(name="人民币").item_ptr,
					("资产", "应收账款", None), info.sale, ("收入", "营业收入", None))
				__add_commodity_transaction(t, org, repo, info, f)

		#Import
		ts = []
		with open('/tmp/jd.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			bad_orders = set()
			for l in reader:
				order_id = int(get_column_value(title, l, "订单号"))
				#status validation
				status = get_column_value(title, l, "订单状态")
				if status not in Jdorder.statuses():
					print "[京东订单]发现新的订单状态: {}".format(status)
					bad_orders.add(order_id)

				#add Jdcommodity
				jdcid = int(get_column_value(title, l, "商品ID"))
				try:
					jdc = Jdcommodity.objects.get(id=jdcid)
				except Jdcommodity.DoesNotExist as e:
					jdc = Jdcommodity(id=jdcid)
				jdc.name=get_column_value(title, l, "商品名称")
				jdc.save()

				#jdcommodity mapping validation
				booktime = utc_2_datetime(cst_2_utc(get_column_value(title, l, "下单时间"), "%Y-%m-%d %H:%M:%S"))
				if not Jdcommoditymap.get(jdc, booktime):
					print "{}) {}:{} 缺乏商品信息".format(booktime.astimezone(timezone.get_current_timezone()), jdc.id, get_column_value(title, l, "商品名称"))
					bad_orders.add(order_id)

				#ignore invalid order
				if order_id in bad_orders:
					continue

				found = False
				for t in ts:
					if t.id == order_id:
						found = True
						break
				if not found:
					t = Jdtransaction()
					t.id = order_id
					t.sale = Decimal(get_column_value(title, l, "应付金额"))
					t.remark = get_column_value(title, l, "商家备注")
					t.booktime = booktime
					t.status = status
					t.invoices = []
					ts.append(t)

				invc = Jdinvoice()
				invc.id = jdc.id
				invc.name = jdc.name
				invc.number = int(get_column_value(title, l, "订购数量"))
				invc.status = status
				invc.depository = get_column_value(title, l, "仓库名称")
				t.invoices.append(invc)

			org = Organization.objects.get(name="为绿厨具专营店")
			repo = Repository.objects.get(name="孤山仓")
			for t in ts:
				t.invoices = sorted(t.invoices, key = lambda i: (i.id * 100000 + i.number))
				__handle_transaction(t, org, repo)
