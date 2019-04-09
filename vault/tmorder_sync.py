# -*- coding: utf-8 -*-
from django.db import transaction
from ground import *
from tmorder import *
from .models import Address
from .models import Customer
from .models import Contact

def cancel_shipping_transaction(task):
	for i in task.transactions.filter(desc__contains=".出货.").order_by("id"):
		splits = i.splits.order_by("account__category", "change")
		s = splits[0]
		s.account = Account.get_or_create(s.account.organization, s.account.item, "支出", "出货", s.account.repository)
		s.change = -splits[1].change
		s.save()

def import_tm_order_list():
	def __handle_list(order_id, time, status, sale, organization, repository, remark, address, phone, name):
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
			("金牌试客", re.compile("^'金"), True),
			("QQ代放", re.compile("^'高"), True),
			("地推代放", re.compile("^'崔"), True),
			("微信", re.compile("^'刘"), True),
		)
		for mark_as, criteria, add in __mapping:
			if criteria.search(remark):
				if add:
					if o.counterfeit and o.counterfeit.name != mark_as:
						print "[警告!!!]天猫订单{}: 备注为{}刷单，当前为{}刷单".format(o.oid, mark_as, o.counterfeit.name)
					elif not o.counterfeit:
						print "天猫订单{}: 备注为{}刷单".format(o.oid, mark_as)
						o.counterfeit = Counterfeit.objects.get(name=mark_as)
						if mark_as == '微信':
							o.counterfeit_auto_clear = True
							cash = Money.objects.get(name="人民币")
							a = Account.get_or_create(organization, cash.item_ptr, "支出", "微信刷单", None)
							b = Account.get(organization.root(), cash.item_ptr, "资产", '运营资金.微信', None)
							Transaction.add(o.task_ptr, "返现", timezone.now(), a, 6, b)
				else:
					if not o.counterfeit or o.counterfeit.name != mark_as:
						print "[警告!!!]天猫订单{}: 备注为{}刷单，系统未标记".format(o.oid, mark_as)
				break

		#collect customer information
		if o.address == None:
			a = Address.add(address)
			if a:
				o.address = a
		join = time_2_seconds(time)
		counterfeit_flag = False
		if o.counterfeit:
			counterfeit_flag = True
		if Contact.objects.filter(phone=phone).exists():
			con = Contact.objects.get(phone=phone)
			cus = con.customer
			if name not in cus.name.split(','):
				cus.name += ',' + name
			if cus.join >= join:
				cus.join = join
				cus.counterfeit = counterfeit_flag
			cus.name = cus.name.decode('utf-8')[-30:]
			cus.save()
		else:
			name = name.decode('utf-8')[-30:]
			cus = Customer(name=name, join=join, counterfeit=counterfeit_flag)
			cus.save()
			con = Contact(phone=phone, customer=cus)
			con.save()
		o.contact = con
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
		address = get_column_value(title, line, "收货地址 ")
		phone = get_column_value(title, line, "联系手机")
		if phone == "'null":
			phone = get_column_value(title, line, "联系电话 ")
			print phone
		phone = phone[1:]
		name = get_column_value(title, line, "收货人姓名")
		with transaction.atomic():
			org = Organization.objects.get(name="泰福高腾复专卖店")
			t = now().replace(year=2019, month=4, day=10, hour=0, minute=0, second=0, microsecond = 0)
			if when > t:
				repo = Repository.objects.get(name="南京仓")
			else:
				repo = Repository.objects.get(name="孤山仓")
				if re.compile("南京仓").search(remark):
					repo = Repository.objects.get(name="南京仓")
			__handle_list(order_id, when, status, sale, org, repo, remark, address, phone, name)
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
