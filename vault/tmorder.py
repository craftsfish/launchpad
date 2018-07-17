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
from django.utils import timezone
from django.db import transaction
from order import *
from turbine import *

class Tmorder(Order, Task):
	oid = models.BigIntegerField("订单编号", unique=True)
	TM_ORDER_STATUS = (
		(0, "等待买家付款"),
		(1, "买家已付款，等待卖家发货"),
		(2, "卖家已发货，等待买家确认"),
		(3, "交易成功"),
		(4, "交易关闭"),
	)
	status = models.IntegerField("状态", choices=TM_ORDER_STATUS, null=True, blank=True)

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
		def __handle_list(order_id, time, status, sale, fake, organization, repository, remark):
			o, created = Tmorder.objects.get_or_create(oid=order_id, desc="天猫订单")
			o.status = Tmorder.str2status(status)
			o.repository = repository
			o.time = time
			o.sale = sale
			if fake:
				if o.counterfeit and o.counterfeit.name != "人气无忧":
					print "{} {}的刷单状态和备注不一致".format(o, o.oid)
				else:
					o.counterfeit = Counterfeit.objects.get(name="人气无忧")
			if re.compile("刘").search(remark):
				if not o.counterfeit or o.counterfeit.name != "微信":
					print "[警告]{}: {}平台备注为微信刷单，没有录入系统".format(o.time.astimezone(timezone.get_current_timezone()), o.oid)
			o.save()

		with open('/tmp/tm.list.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			org = Organization.objects.get(name="泰福高腾复专卖店")
			for i in reader:
				with transaction.atomic():
					status = get_column_value(title, i, "订单状态")
					if status not in Tmorder.statuses():
						print "[天猫]未知订单状态: {}".format(status)
						continue
					order_id = int(re.compile(r"\d+").search(get_column_value(title, i, "订单编号")).group())
					when = utc_2_datetime(cst_2_utc(get_column_value(title, i, "订单创建时间"), "%Y-%m-%d %H:%M:%S"))
					sale = Decimal(get_column_value(title, i, "买家应付货款"))
					remark = get_column_value(title, i, "订单备注")
					f = 0
					if remark.find("朱") != -1:
						f = 1
					repo = Repository.objects.get(name="孤山仓")
					if re.compile("南京仓").search(remark):
						repo = Repository.objects.get(name="南京仓")

					__handle_list(order_id, when, status, sale, f, org, repo, remark)
