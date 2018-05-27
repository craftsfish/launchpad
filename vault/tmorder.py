# -*- coding: utf-8 -*-
import csv
import re
from django.db import models
from task import *
from ground import *
from tmcommodity import *
from organization import *
from account import *
from decimal import Decimal
from util import *
from django.utils import timezone

class Tmorder(models.Model):
	id = models.BigIntegerField("订单编号", primary_key=True)
	TM_ORDER_STATUS = (
		(0, "等待买家付款"),
		(1, "买家已付款，等待卖家发货"),
		(2, "卖家已发货，等待买家确认"),
		(3, "交易成功"),
		(4, "交易关闭"),
	)
	status = models.IntegerField("状态", choices=TM_ORDER_STATUS)
	task = models.OneToOneField(Task)
	fake = models.IntegerField("刷单", default=0)
	time = models.DateTimeField(default=timezone.now)

	@staticmethod
	def statuses():
		r = []
		for i, v in Tmorder.TM_ORDER_STATUS:
			r.append(v)
		return r

	@staticmethod
	def str2status(s):
		for i, v in Tmorder.TM_ORDER_STATUS:
			if v == s:
				return i
		return -1

	@staticmethod
	def Import_List():
		#增加一条刷单Transaction
		def __add_fake_transaction(task, organization, repository, time):
			c = Commodity.objects.get(name="洗衣粉")
			Transaction.add(task, "0.出货.{}".format(c.name), time, organization, c.item_ptr,
				("资产", "完好", repository), -1, ("支出", "出货", repository))

		def __handle_list(order_id, time, status, sale, fake, organization, repository):
			try: #更新
				o = Tmorder.objects.get(id=order_id)
				if status == "交易关闭":
					for t in o.task.transactions.all():
						t.delete()
					return
				if o.fake != fake:
					for t in o.task.transactions.filter(desc__contains='.出货.'):
						t.delete()
					if fake:
						__add_fake_transaction(o.task, organization, repository, time)
				o.status = Tmorder.str2status(status)
				o.fake = fake
				o.save()
			except Tmorder.DoesNotExist as e: #新增
				t = Task(desc="天猫订单")
				t.save()
				o = Tmorder(id=order_id, status=Tmorder.str2status(status), task=t, fake=fake, time=time)
				o.save()
				if status == "交易关闭":
					return
				Transaction.add(t, "出单", time, organization, Money.objects.get(name="人民币").item_ptr,
					("资产", "应收账款", None), sale, ("收入", "营业收入", None))
				if fake:
					__add_fake_transaction(t, organization, repository, time)

		with open('/tmp/tm.list.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			org = Organization.objects.get(name="泰福高腾复专卖店")
			repo = Repository.objects.get(name="孤山仓")
			for i in reader:
				status = get_column_value(title, i, "订单状态")
				if status not in Tmorder.statuses():
					print "[天猫]未知订单状态: {}".format(status)
					continue
				order_id = int(re.compile(r"\d+").search(get_column_value(title, i, "订单编号")).group())
				when = utc_2_datetime(cst_2_utc(get_column_value(title, i, "订单创建时间"), "%Y-%m-%d %H:%M:%S"))
				sale = Decimal(get_column_value(title, i, "买家应付货款"))
				remark = get_column_value(title, i, "订单备注")
				f = False
				if remark.find("朱") != -1:
					f = True

				__handle_list(order_id, when, status, sale, f, org, repo)

	@staticmethod
	def Import_Detail():
		def __handle_detail(order, commodity, status, quantity, organization, repository):
			m = Tmcommoditymap.get(commodity, order.time)
			if m == None:
				print "商家编码: {}还没有商品映射信息".format(commodity.id)
				return

			#retrieve existing status
			future_out = False
			if order.task.transactions.filter(desc__startswith="期货出货."+commodity.id).count():
				future_out = True
			future_deliver = False
			if order.task.transactions.filter(desc__startswith="期货发货."+commodity.id).count():
				future_deliver = True

			#update
			if status in ["等待买家付款", "交易关闭"] and future_out:
				order.task.delete_transactions_start_with("期货出货."+commodity.id, "期货发货."+commodity.id, "出库."+commodity.id)
				return

			if status in ["买家已付款，等待卖家发货", "卖家已发货，等待买家确认", "交易成功"] and not future_out:
				for item in m:
					Shipping.future_out(order.task, order.time, organization, item, quantity, commodity.id)

			if status in ["卖家已发货，等待买家确认", "交易成功"] and not future_deliver:
				for item in m:
					Shipping.future_deliver(order.task, order.time, organization, item, quantity, repository, "完好", commodity.id)

		with open('/tmp/tm.detail.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			org = Organization.objects.get(name="泰福高腾复专卖店")
			repo = Repository.objects.get(name="孤山仓")
			for i in reader:
				oid = int(re.compile(r"\d+").search(get_column_value(title, i, "订单编号")).group())
				o = Tmorder.objects.get(pk=oid)
				if o.fake or o.status == Tmorder.str2status("交易关闭"):
					continue

				cid = get_column_value(title, i, "商家编码")
				if cid == "null":
					print "订单{}缺少商家编码".format(oid)
					continue
				c = Tmcommodity.objects.get(pk=cid)
				status = get_column_value(title, i, "订单状态")
				quantity = int(get_column_value(title, i, "购买数量"))

				__handle_detail(o, c, status, quantity, org, repo)
