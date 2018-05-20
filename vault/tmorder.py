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
		def __handle_list(order_id, time, status, sale, fake, organization, repository):
			if status not in Tmorder.statuses():
				print "[天猫]未知订单状态: {}".format(status)
				return

			try: #更新
				o = Tmorder.objects.get(id=order_id)
				if status == "交易关闭":
					for t in o.task.transactions.all():
						t.delete()
					return
				if o.fake != fake:
					for t in o.task.transactions.filter(desc__in=["期货出货", "期货发货", "出库"]):
						t.delete()
					if fake:
						Shipping.future_out(o.task, time, organization, Item.objects.get(name="洗衣粉"), 1)
						task_future_deliver(o.task, repository)
				o.status = Tmorder.str2status(status)
				o.fake = fake
				o.save()
			except Tmorder.DoesNotExist as e: #新增
				t = Task(desc="天猫订单")
				t.save()
				o = Tmorder(id=order_id, status=Tmorder.str2status(status), task=t, fake=fake)
				o.save()
				if status == "交易关闭":
					return
				t.add_transaction("出单", time, organization, Item.objects.get(name="人民币"), ("资产", "应收账款"), sale, ("收入", "营业收入"))
				if fake:
					Shipping.future_out(t, time, organization, Item.objects.get(name="洗衣粉"), 1)
					task_future_deliver(t, repository)

		with open('/tmp/tm.list.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			org = Organization.objects.get(name="泰福高腾复专卖店")
			repo = Organization.objects.get(name="孤山仓")
			for i in reader:
				order_id = int(re.compile(r"\d+").search(get_column_value(title, i, "订单编号")).group())
				status = get_column_value(title, i, "订单状态")
				when = utc_2_datetime(cst_2_utc(get_column_value(title, i, "订单创建时间"), "%Y-%m-%d %H:%M:%S"))
				sale = Decimal(get_column_value(title, i, "买家应付货款"))
				remark = get_column_value(title, i, "订单备注")
				f = False
				if remark.find("朱") != -1:
					f = True

				__handle_list(order_id, when, status, sale, f, org, repo)

	@staticmethod
	def Import_Detail():
		with open('/tmp/tm.detail.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			org = Organization.objects.get(name="泰福高腾复专卖店")
			repo = Organization.objects.get(name="孤山仓")
			for i in reader:
				oid = int(re.compile(r"\d+").search(get_column_value(title, i, "订单编号")).group())
				cid = get_column_value(title, i, "商家编码")
				if cid == "null":
					print "订单{}缺少商家编码".format(oid)
					continue
				c = Tmcommodity.objects.get(pk=cid)
				o = Tmorder.objects.get(pk=oid)
				status = get_column_value(title, i, "订单状态")
				quantity = int(get_column_value(title, i, "购买数量"))
