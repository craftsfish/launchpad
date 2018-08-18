# -*- coding: utf-8 -*-
import csv
import re
from ground import *
from django.db import models
from task import *
from ground import *
from jdcommodity import *
from organization import *
from account import *
from decimal import Decimal
from django.db import transaction
from order import *
from turbine import *

class Jdorder(Order, Task):
	oid = models.BigIntegerField("订单编号", unique=True)
	JD_ORDER_STATUS = (
		(0, "等待出库"),
		(1, "等待确认收货"),
		(2, "完成"),
		(3, "(删除)锁定"),
		(4, "(删除)等待出库"),
		(5, "(删除)等待确认收货"),
		(6, "锁定"),
	)
	status = models.IntegerField("状态", choices=JD_ORDER_STATUS, null=True, blank=True)

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
	def import_fake_order():
		@transaction.atomic
		def __csv_handler(oid, sale, fee):
			org = Organization.objects.get(name="为绿厨具专营店")
			if not Jdorder.objects.filter(oid=oid).exists():
				print "订单未导入: {}".format(oid)
				return
			o = Jdorder.objects.get(oid=oid)
			if not o.task_ptr.transactions.filter(desc="刷单.结算.陆凤").exists():
				if o.counterfeit.name != "陆凤":
					print "订单未标记为陆凤刷单: {}".format(oid)
					return
				if o.sale != sale:
					print "订单金额不对: {}".format(oid)
					return
				cash = Money.objects.get(name="人民币")
				a = Account.get(org.root(), cash.item_ptr, "负债", "陆凤刷单", None)
				b = Account.get(org, cash.item_ptr, "支出", "陆凤刷单", None)
				Transaction.add(o.task_ptr, "刷单.结算.陆凤", timezone.now(), a, sale+fee, b)
			else:
				print "订单已经结算: {}".format(oid)

		with open('/tmp/jd.fake.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			title = reader.next()
			columns = ["订单编号", "金额", "佣金"]
			for l in reader:
				order_id, sale, fee = get_column_values(title, l, *columns)
				print "刷单 | 订单编号: {} | 订单金额: {} | 费用 : {}".format(order_id, sale, fee)
				__csv_handler(order_id, Decimal(sale), Decimal(fee))
