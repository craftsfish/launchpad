# -*- coding: utf-8 -*-
from django.db import transaction
from ground import *
from tmorder import *

def cancel_shipping_transaction(task):
	for i in task.transactions.filter(desc__contains=".出货.").order_by("id"):
		splits = i.splits.order_by("account__category", "change")
		s = splits[0]
		s.account = Account.get_or_create(s.account.organization, s.account.item, "支出", "出货", s.account.repository)
		s.change = -splits[1].change
		s.save()

def import_tm_order_list():
	def __handle_list(order_id, time, status, sale, organization, repository, remark):
		#preparation
		o, created = Tmorder.objects.get_or_create(oid=order_id, desc="天猫订单")
		o.status = Tmorder.str2status(status)
		o.repository = repository
		o.time = time
		o.sale = sale

		#counterfeit handling
		__mapping = (
			#platform, filter, add(True) or verify counterfeit info
			("人气无忧", re.compile("^'朱"), True),
			("威客圈", re.compile("^'伟"), True),
			("微信", re.compile("^'刘"), False),
		)
		for mark_as, criteria, add in __mapping:
			if criteria.search(remark):
				if add:
					if o.counterfeit and o.counterfeit.name != mark_as:
						print "[警告!!!]天猫订单{}: 备注为{}刷单，当前为{}刷单".format(o.oid, mark_as, o.counterfeit.name)
					elif not o.counterfeit:
						print "天猫订单{}: 备注为{}刷单".format(o.oid, mark_as)
						o.counterfeit = Counterfeit.objects.get(name=mark_as)
				else:
					if not o.counterfeit or o.counterfeit.name != mark_as:
						print "[警告!!!]天猫订单{}: 备注为{}刷单，系统未标记".format(o.oid, mark_as)
				break

		#save
		o.save()
		if status == "交易关闭": #商品明细有可能不出现在详情表中
			cancel_shipping_transaction(o.task_ptr)

	def __handler(title, line, *args):
		status = get_column_value(title, line, "订单状态")
		if status not in Tmorder.statuses():
			print "[天猫]未知订单状态: {}".format(status)
			return
		order_id = int(re.compile(r"\d+").search(get_column_value(title, line, "订单编号")).group())
		when = utc_2_datetime(cst_2_utc(get_column_value(title, line, "订单创建时间"), "%Y-%m-%d %H:%M:%S"))
		sale = Decimal(get_column_value(title, line, "买家应付货款"))
		remark = get_column_value(title, line, "订单备注")
		with transaction.atomic():
			org = Organization.objects.get(name="泰福高腾复专卖店")
			repo = Repository.objects.get(name="孤山仓")
			if re.compile("南京仓").search(remark):
				repo = Repository.objects.get(name="南京仓")
			__handle_list(order_id, when, status, sale, org, repo, remark)
	csv_parser('/tmp/tm.list.csv', csv_gb18030_2_utf8, True, __handler)

class Tmtransaction:
	pass
class Tminvoice:
	pass

def import_tm_order_detail():
	@transaction.atomic
	def __handle_detail(info, organization):
		o = Tmorder.objects.get(oid=info.oid)
		info.invoices = sorted(info.invoices, key = lambda i: (i.id + str(i.number)))
		for i, v in enumerate(info.invoices, 1):
			if v.status in ["等待买家付款", "买家已付款，等待卖家发货", "卖家部分发货"]:
				delivery = DeliveryStatus.inbook
			elif v.status in ["卖家已发货，等待买家确认", "交易成功"]:
				delivery = DeliveryStatus.delivered
			else:
				delivery = DeliveryStatus.cancel
			commodities = Tmcommoditymap.get(Tmcommodity.objects.get(pk=v.id), o.time)
			o.create_or_update_invoice_shipment(organization, i, v.id, commodities, v.number, delivery)
		o.update()

	def __handler_transaction_raw(info):
		if not info: return
		org = Organization.objects.get(name="泰福高腾复专卖店")
		for i in info.invoices:
			if i.id == "null": #如果没有设定商家编码，系统无法对现有订单的商品追加，仅提供警告信息
				print "订单{}没有设定商家编码".format(info.oid)
			if i.status not in Tmorder.statuses():
				print "[天猫订单]发现新的订单状态: {}".format(i.status)
				info.bad = True
				break

			with transaction.atomic():
				tmc, created = Tmcommodity.objects.get_or_create(id=i.id)
				tmc.name=i.name
				tmc.save()
				o = Tmorder.objects.get(oid=info.oid)
				if not Tmcommoditymap.get(tmc, o.time):
					print "{}) {}:{} 缺乏商品信息".format(o.time.astimezone(timezone.get_current_timezone()), tmc.id, tmc.name)
					info.bad = True
					break

		if not info.bad:
			__handle_detail(info, org)

	def __handler(title, line, *args):
		parameters = args[0]
		prev_transaction = parameters[0]

		exp = re.compile(r"\d+").search(get_column_value(title, line, "订单编号"))
		if not exp: return
		order_id = int(exp.group())
		if prev_transaction and prev_transaction.oid == order_id: #same order, merge with previous line
			cur_transaction = prev_transaction
		else:
			t = Tmtransaction()
			t.bad = False
			t.oid = order_id
			t.invoices = []
			cur_transaction = t

		#append current invoice
		invc = Tminvoice()
		invc.id = get_column_value(title, line, "商家编码")
		invc.name =get_column_value(title, line, "标题")
		invc.number = int(get_column_value(title, line, "购买数量"))
		invc.status = get_column_value(title, line, "订单状态")
		cur_transaction.invoices.append(invc)

		#sync
		if cur_transaction != prev_transaction:
			parameters[0] = cur_transaction #update prev_transaction with current one
			__handler_transaction_raw(prev_transaction)

	#main
	parameters=[None]
	csv_parser('/tmp/tm.detail.csv', csv_gb18030_2_utf8, True, __handler, parameters)
	__handler_transaction_raw(parameters[0]) #handle last transaction
