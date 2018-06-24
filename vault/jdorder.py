# -*- coding: utf-8 -*-
import csv
import re
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
	fake = models.IntegerField("刷单", default=0) #TODO, remove me and using conterfeit instead

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
				commodities = Jdcommoditymap.get(Jdcommodity.objects.get(pk=v.id), info.booktime)
				if info.status == "等待出库":
					delivered = False
				else:
					delivered = True
				Order.invoice_shipment_create(task, info.booktime, organization, repository, i+1, v.id, commodities, v.number, delivered)

		#增加一条刷单Transaction
		def __add_fake_transaction(task, organization, repository, info):
					c = Commodity.objects.get(name="洗衣粉")
					Transaction.add_raw(task, "0.出货.{}".format(c.name), info.booktime, organization, c.item_ptr,
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
			if re.compile("朱").search(info.remark): #fake order
				f = 1
			try:
				o = Jdorder.objects.get(oid=info.id)
				if info.status in ["(删除)锁定", "(删除)等待出库", "(删除)等待确认收货"]:
					o.task_ptr.delete_transactions_contains_desc('.出货.')
					return

				if info.status == "等待出库":
					delivered = False
				else:
					delivered = True
				if o.task_ptr.transactions.filter(desc__contains=".出货.").exists():
					for i in range(len(info.invoices)):
						Order.invoice_shipment_update_status(o.task_ptr, i+1, delivered)
				else:
					for i, v in enumerate(info.invoices):
						commodities = Jdcommoditymap.get(Jdcommodity.objects.get(pk=v.id), info.booktime)
						Order.invoice_shipment_create(o.task_ptr, info.booktime, org, repo, i+1, v.id, commodities, v.number, delivered)

				o.status = Jdorder.str2status(info.status)
				if o.counterfeit:
					if f and o.counterfeit.name != "陆凤":
						print "{} {}刷单状态和备注不一致".format(o, o.oid)
				else:
					if f:
						o.counterfeit = Counterfeit.objects.get(name="陆凤")
				o.repository = repo
				o.sale = info.sale
				o.save()

				o.update()
			except Jdorder.DoesNotExist as e:
				o = Jdorder(oid=info.id, status=Jdorder.str2status(info.status), desc="京东订单", fake=f, repository=repo, sale=info.sale)
				o.save()
				if info.status in ["(删除)锁定", "(删除)等待出库", "(删除)等待确认收货"]:
					return #no transaction should be added
				__add_commodity_transaction(o.task_ptr, org, repo, info, f)

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
			if not o.task_ptr.transactions.filter(desc="陆凤刷单.结算").exists():
				if o.fake != 1:
					print "订单未标记为刷单: {}".format(oid)
					return
				if o.sale != sale:
					print "订单金额不对: {}".format(oid)
					return
				cash = Money.objects.get(name="人民币")
				a = Account.get(org.root(), cash.item_ptr, "负债", "陆凤刷单", None)
				b = Account.get(org, cash.item_ptr, "支出", "陆凤刷单", None)
				Transaction.add(o.task_ptr, "陆凤刷单.结算", timezone.now(), a, sale+fee, b)
			else:
				print "订单已经结算: {}".format(oid)

		with open('/tmp/jd.fake.csv', 'rb') as csvfile:
			orgs = Organization.objects.filter(parent=None).exclude(name="个人")
			reader = csv.reader((csvfile))
			title = reader.next()
			columns = ["订单编号", "金额", "佣金"]
			for l in reader:
				order_id, sale, fee = get_column_values(title, l, *columns)
				print "刷单 | 订单编号: {} | 订单金额: {} | 费用 : {}".format(order_id, sale, fee)
				__csv_handler(order_id, Decimal(sale), Decimal(fee))
