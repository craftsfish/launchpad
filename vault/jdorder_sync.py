# -*- coding: utf-8 -*-
from ground import *
from jdorder import *
from django.db import transaction

class Jdtransaction:
	pass
class Jdinvoice:
	pass

def import_jd_order():
	def __transaction_dump(info):
		print "{}, {} | {} | 销售额: {}".format(info.booktime, info.id, info.status, info.sale)
		for i in info.invoices:
			print "{}, {}, {}, {}".format(i.id, i.name, i.number, i.status)

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

	def __handler_transaction_raw(info):
		if info and not info.bad:
			with transaction.atomic():
				org = Organization.objects.get(name="为绿厨具专营店")
				info.invoices = sorted(info.invoices, key = lambda i: (i.id * 100000 + i.number))
				repo = Repository.objects.get(name="孤山仓")
				if re.compile("南京仓").search(info.remark):
					repo = Repository.objects.get(name="南京仓")
				__handle_transaction(info, org, repo)

	def __handler(title, line, *args):
		parameters = args[0]
		prev_transaction = parameters[0]

		order_id = int(get_column_value(title, line, "订单号"))
		status = get_column_value(title, line, "订单状态")
		booktime = utc_2_datetime(cst_2_utc(get_column_value(title, line, "下单时间"), "%Y-%m-%d %H:%M:%S"))
		if prev_transaction and prev_transaction.id == order_id: #same order, merge with previous line
			cur_transaction = prev_transaction
		else:
			t = Jdtransaction()
			t.bad = False
			t.id = order_id
			t.sale = Decimal(get_column_value(title, line, "应付金额"))
			t.remark = get_column_value(title, line, "商家备注")
			t.booktime = booktime
			t.status = status
			t.invoices = []
			cur_transaction = t

		if status not in Jdorder.statuses():
			print "[京东订单]发现新的订单状态: {}".format(status)
			cur_transaction.bad = True

		#add Jdcommodity
		jdcid = int(get_column_value(title, line, "商品ID"))
		with transaction.atomic():
			jdc, created = Jdcommodity.objects.get_or_create(id=jdcid)
			jdc.name=get_column_value(title, line, "商品名称")
			jdc.save()

		#jdcommodity mapping validation
		if not Jdcommoditymap.get(jdc, booktime):
			print "{}) {}:{} 缺乏商品信息".format(booktime.astimezone(timezone.get_current_timezone()), jdc.id, get_column_value(title, l, "商品名称"))
			cur_transaction.bad = True

		#add invoice
		invc = Jdinvoice()
		invc.id = jdc.id
		invc.name = jdc.name
		invc.number = int(get_column_value(title, line, "订购数量"))
		invc.status = status
		invc.depository = get_column_value(title, line, "仓库名称")
		cur_transaction.invoices.append(invc)

		#sync
		if cur_transaction != prev_transaction:
			parameters[0] = cur_transaction #update prev_transaction with current one
			__handler_transaction_raw(prev_transaction)

	#main
	parameters=[None]
	csv_parser('/tmp/jd.csv', csv_gb18030_2_utf8, True, __handler, parameters)
	__handler_transaction_raw(parameters[0]) #handle last transaction
