# -*- coding: utf8 -*-
import csv
from ground import *
from datetime import datetime
from django.utils import timezone
from tmorder import *
from jdorder import *
from decimal import Decimal
from express import *

class Sync(object):
	@staticmethod
	@transaction.atomic
	def rqwy():
		def __handler(org, when, status, request, bill, commission, order_id):
			discount = Decimal(0.7)
			if order_id == "":
				print "{}: 冻结资金{}".format(when, request+1 + (commission+1)*discount)
				return request+1 + (commission+1)*discount
			order_id = int(order_id)
			if not Tmorder.objects.filter(oid=order_id).exists():
				return 0
			order = Tmorder.objects.get(oid=order_id)
			if not order.counterfeit:
				order.counterfeit = Counterfeit.objects.get(name="人气无忧")
			if order.counterfeit.name != "人气无忧":
				print "{}, 人气无忧订单被标记为{}刷单".format(order, order.counterfeit)
				return 0
			if order.sale != bill:
				print "{}, {}, 人气无忧订单金额不一致".format(when, order)
			if not order.task_ptr.transactions.filter(desc="刷单.结算.人气无忧").exists():
				cash = Money.objects.get(name="人民币")
				a = Account.get(org.root(), cash.item_ptr, "资产", "运营资金.人气无忧", None)
				b = Account.get(org, cash.item_ptr, "支出", "人气无忧刷单", None)
				Transaction.add(order.task_ptr, "刷单.结算.人气无忧", when, a, -bill-1-(commission+1)*discount, b)
			return 0
		organization = Organization.objects.get(name="泰福高腾复专卖店")
		frozen = 0
		for f in ['/tmp/rqwy.finished.csv', '/tmp/rqwy.unfinished.csv']:
			with open(f, 'rb') as csvfile:
				reader = csv.reader((csvfile))
				title = reader.next()
				for l in reader:
					when, status, request, bill, commission, order_id = get_column_values(title, l, "接单时间", "订单状态", "垫付金额", "用户支付金额", "任务佣金", "用户提交订单ID")
					t = datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
					when = datetime.now(timezone.get_current_timezone()).replace(*(t.timetuple()[0:6])).replace(microsecond=0)
					frozen += __handler(organization, when, status, Decimal(request), Decimal(bill), Decimal(commission), order_id)
		total = get_decimal_with_default(Account.objects.filter(name='运营资金.人气无忧').aggregate(Sum('balance'))['balance__sum'], 0)
		print "账面剩余资金: {} - 冻结资金: {} = 账户留存资金: {}".format(total, frozen, total - frozen)

	@staticmethod
	def __express_creator(title, line, columns):
		supplier, serial = get_column_values(title, line, *columns)
		serial = re.compile(r"\D+").sub("", serial)
		if serial == "":
			return None
		serial = int(serial)
		sp = None
		for s, l in express_supplier_map:
			ExpressSupplier.objects.get_or_create(name=s)
			if supplier in l:
				sp = s
				break
		if not sp:
			print "{} 无法匹配任何现有快递服务商!".format(supplier)
			return None

		express, created = Express.objects.get_or_create(eid=serial, supplier=ExpressSupplier.objects.get(name=sp))
		if created:
			print "增加快递单: {}, {}".format(sp, serial)
		return express

	@staticmethod
	def import_tm_express():
		@transaction.atomic
		def __handler(title, line, *args):
			e = Sync.__express_creator(title, line, ["物流公司", "物流单号 "])
			if not e:
				return
			order_id = int(re.compile(r"\d+").search(get_column_value(title, line, "订单编号")).group())
			e.task = Tmorder.objects.get(oid=order_id).task_ptr
			e.save()
		csv_parser('/tmp/tm.list.csv', csv_gb18030_2_utf8, True, __handler)

	@staticmethod
	def import_jd_express():
		@transaction.atomic
		def __handler(title, line, *args):
			e = Sync.__express_creator(title, line, ["快递公司", "快递单号"])
			if not e:
				return
			order_id = int(get_column_value(title, line, "订单号"))
			e.task = Jdorder.objects.get(oid=order_id).task_ptr
			e.save()
		csv_parser('/tmp/jd.express.csv', csv_gb18030_2_utf8, True, __handler)

	@staticmethod
	def import_existing_express():
		@transaction.atomic
		def __handler(title, line, *args):
			e = Sync.__express_creator(title, line, ["服务商", "快递单号"])
			if not e:
				return
			c = get_column_value(title, line, "结算")
			if c == "1" and not e.clear:
				print "{} 标记为已结算".format(e)
				e.clear = True
				e.save()
		csv_parser('/tmp/express.csv', None, True, __handler)

	@staticmethod
	def __express_clear(clear, supplier, column_eid, column_amount, append_expresses):
		@transaction.atomic
		def __handler(title, line, *args):
			nsupplier, neid, namount = args[0][1:4]
			serial, amount = get_column_values(title, line, neid, namount)
			serial = int(serial)
			amount = Decimal(amount)
			supplier=ExpressSupplier.objects.get(name=nsupplier)
			if Express.objects.filter(eid=serial).filter(supplier=supplier).exists():
				e = Express.objects.get(eid=serial, supplier=supplier)
				if e.clear:
					print "{} 已经结算".format(csv_line_2_str(line))
					return
				args[0][0] += amount
				if clear:
					e.clear = True
					e.fee = amount
					e.save()
			else:
				if serial in args[1]: #add forcefully
					if clear:
						Express(eid=serial, supplier=supplier, clear=True, fee=amount).save()
					args[0][0] += amount
				else:
					print "{} 不存在".format(csv_line_2_str(line))
		misc = [0, supplier, column_eid, column_amount]
		csv_parser('/tmp/express.csv', None, True, __handler, misc, append_expresses)
		print "有效订单合计: {}".format(misc[0])

	@staticmethod
	def import_zt_express():
		Sync.__express_clear(False, '中通', "运单编号", "金额", [])
