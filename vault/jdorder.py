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

class Jdtransaction:
	pass

class Jdinvoice:
	pass

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
	def Import():
		def __handle_transaction(info, org, repo):
			#collect necessary information
			o, created = Jdorder.objects.get_or_create(oid=info.id, desc="京东订单")
			o.status = Jdorder.str2status(info.status)
			o.repository = repo
			o.time = info.booktime
			o.sale = info.sale
			if re.compile("朱").search(info.remark): #陆凤刷单
				if o.counterfeit and o.counterfeit.name != "陆凤":
					print "{} {}的刷单状态和备注不一致".format(o, o.oid)
				else:
					o.counterfeit = Counterfeit.objects.get(name="陆凤")

			#apply
			if info.status == "等待出库":
				delivery = DeliveryStatus.inbook
			elif info.status in ["等待确认收货", "完成"]:
				delivery = DeliveryStatus.delivered
			else:
				delivery = DeliveryStatus.cancel
			for i, v in enumerate(info.invoices, 1):
				commodities = Jdcommoditymap.get(Jdcommodity.objects.get(pk=v.id), info.booktime)
				o.create_or_update_invoice_shipment(org, i, v.id, commodities, v.number, delivery)
			o.update()
			o.save()

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
				with transaction.atomic():
					jdc, created = Jdcommodity.objects.get_or_create(id=jdcid)
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
			for t in ts:
				if t.id in bad_orders:
					continue
				with transaction.atomic():
					t.invoices = sorted(t.invoices, key = lambda i: (i.id * 100000 + i.number))
					repo = Repository.objects.get(name="孤山仓")
					if re.compile("南京仓").search(t.remark):
						repo = Repository.objects.get(name="南京仓")
					__handle_transaction(t, org, repo)

	@staticmethod
	def import_fake_order():
		@transaction.atomic
		def __csv_handler(oid, sale, fee):
			org = Organization.objects.get(name="为绿厨具专营店")
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
