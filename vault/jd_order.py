# -*- coding: utf-8 -*-

import csv
from django.db import models
from task import *
from ground import *
from jdcommodity import *

class Jdorder(models.Model):
	id = models.BigIntegerField("订单编号", primary_key=True)
	JD_ORDER_STATUS = (
		(0, " 等待出库"),
		(1, " 等待确认收货"),
		(2, " 完成"),
		(3, " (删除)锁定"),
		(4, " (删除)等待出库"),
		(5, " (删除)等待确认收货"),
	)
	status = models.IntegerField("状态", choices=JD_ORDER_STATUS)
	task = models.OneToOneField(Task)

	@staticmethod
	def Import():
		exit = False
		with open('/tmp/jd.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			for l in reader:
				jdc = int(get_column_value(title, l, "商品ID"))
				booktime = utc_2_datetime(cst_2_utc(get_column_value(title, l, "下单时间"), "%Y-%m-%d %H:%M:%S"))
				items = Jdcommoditymap.get(jdc, booktime)
				if items == None:
					exit = True
					print "{}) {}:{} 缺乏商品信息".format(booktime.astimezone(timezone.get_current_timezone()), jdc, get_column_value(title, l, "商品名称"))
		if exit:
			return
