# -*- coding: utf-8 -*-

import csv
from django.db import models
from task import *
from ground import *

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
		with open('/tmp/jd.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			for l in reader:
				jd_commodity = int(get_column_value(title, l, "商品ID"))
				print jd_commodity
