# -*- coding: utf8 -*-
import csv
from ground import *
from datetime import datetime
from django.utils import timezone
from tmorder import *
from decimal import Decimal

class Sync(object):
	@staticmethod
	def rqwy():
		def __handler(org, when, status, request, bill, commission, order_id):
			discount = Decimal(0.7)
			if order_id == "":
				pass #TODO: accumulation of frozen money
				return request + commission*discount
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
				Transaction.add(order.task_ptr, "刷单.结算.人气无忧", when, a, -bill-commission*discount, b)
			return 0
		organization = Organization.objects.get(name="泰福高腾复专卖店")
		frozen = 0
		for f in ['/tmp/rqwy.finished.csv', '/tmp/rqwy.unfinished.csv']:
			with open(f, 'rb') as csvfile:
				reader = csv.reader((csvfile))
				title = reader.next()
				for l in reader:
					when, status, request, bill, commission, order_id = get_column_values(title, l, "接单时间", "订单状态", "商家要求垫付金额", "卖家返款金额", "任务佣金", "买手提交单号")
					t = datetime.strptime(when, "%Y-%m-%d %H:%M:%S.%f")
					when = datetime.now(timezone.get_current_timezone()).replace(*(t.timetuple()[0:6])).replace(microsecond=0)
					frozen += __handler(organization, when, status, Decimal(request), Decimal(bill), Decimal(commission), order_id)
		print "冻结资金: {}".format(frozen)
