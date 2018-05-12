# -*- coding: utf-8 -*-

import csv
from django.db import models
from task import *
from ground import *
from jdcommodity import *

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

	@staticmethod
	def statuses():
		r = []
		for i, v in Jdorder.JD_ORDER_STATUS:
			r.append(v)
		return r

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
						print "{}) {}:{} 缺乏商品信息".format(booktime.astimezone(timezone.get_current_timezone()), jdc, get_column_value(title, l, "商品名称"))
			return result

		def __handle_transaction(t):
			print "[同步订单...] {}: {}".format(t.booktime, t.id)
			pass

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
						t.sale = float(get_column_value(title, l, "应付金额"))
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

				for t in ts:
					__handle_transaction(t)

		if __preliminary_check():
			__import()
		else:
			print "请完善相关信息后重试!!!"
