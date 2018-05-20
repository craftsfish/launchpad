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
				print "[天猫]订单: {}".format(order_id)

				#check
				if status not in Tmorder.statuses():
					print "[天猫]未知订单状态: {}".format(status)
					return

				#sync
				try:
					o = Tmorder.objects.get(id=order_id)
					#TODO: update
				except Tmorder.DoesNotExist as e:
					t = Task(desc="天猫订单")
					t.save()
					print "[添加订单...] {}: {} | 刷单标记: {}".format(order_id, status, f)
					o = Tmorder(id=order_id, status=Tmorder.str2status(status), task=t, fake=f)
					o.save()

					if status == "交易关闭":
						continue
					t.add_transaction("出单", when, org, Item.objects.get(name="人民币"), ("资产", "应收账款"), sale, ("收入", "营业收入"))
					if f:
						Shipping.future_out(t, when, org, Item.objects.get(name="洗衣粉"), 1)
						task_future_deliver(t, repo)
