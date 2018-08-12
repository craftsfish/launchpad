# -*- coding: utf8 -*-
import csv
from ground import *
from datetime import datetime
from django.utils import timezone
from tmorder import *
from jdorder import *
from decimal import Decimal
from express import *
from .models import *
from jdorder_sync import import_jd_order
from tmorder_sync import import_tm_order_list, import_tm_order_detail
from turbine import *

def import_order():
	import_jd_order()
	import_tm_order_list()
	import_tm_order_detail()
	Turbine.update_calibration_window()

@transaction.atomic
def import_rqwy():
	def __handler(title, line, *args):
		latest_orders = args[0]
		pid, when, status, request, bill, commission, order_id = get_column_values(title, line, "订单ID", "接单时间", "订单状态", "垫付金额", "用户支付金额", "任务佣金", "用户提交订单ID")
		t = datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
		when = datetime.now(timezone.get_current_timezone()).replace(*(t.timetuple()[0:6])).replace(microsecond=0)
		request = Decimal(request)
		bill = Decimal(bill)
		commission = Decimal(commission)
		discount = Decimal(0.7)
		if order_id == "":
			latest_orders.append([when, request+1 + commission*discount, "冻结", pid])
			return
		order_id = int(order_id)
		if not Tmorder.objects.filter(oid=order_id).exists():
			if when > datetime.now(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0):
				latest_orders.append([when, bill+1 + commission*discount, "订单未导入", pid])
			return
		if when > datetime.now(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0):
			latest_orders.append([when, bill+1 + commission*discount, "已结算", pid])
		order = Tmorder.objects.get(oid=order_id)
		if not order.counterfeit:
			order.counterfeit = Counterfeit.objects.get(name="人气无忧")
		if order.counterfeit.name != "人气无忧":
			print "{}, 人气无忧订单被标记为{}刷单".format(order, order.counterfeit)
		if order.sale != bill:
			print "{}, {}, 人气无忧订单金额不一致".format(when, order)
		if not order.task_ptr.transactions.filter(desc="刷单.结算.人气无忧").exists():
			org = Organization.objects.get(name="泰福高腾复专卖店")
			cash = Money.objects.get(name="人民币")
			a = Account.get(org.root(), cash.item_ptr, "资产", "运营资金.人气无忧", None)
			b = Account.get(org, cash.item_ptr, "支出", "人气无忧刷单", None)
			Transaction.add(order.task_ptr, "刷单.结算.人气无忧", when, a, -bill-1-commission*discount, b)

	#main
	latest_orders =[]
	csv_parser('/tmp/rqwy.finished.csv', None, True, __handler, latest_orders)
	csv_parser('/tmp/rqwy.unfinished.csv', None, True, __handler, latest_orders)
	def __key(i):
		return i[0]
	unaccounted = 0
	for when, amount, desc, pid in sorted(latest_orders, key=__key, reverse=True):
		print "{},{},{:.2f},{}".format(when, pid, float(amount), desc)
		if desc != "已结算":
			unaccounted += amount
	total = get_decimal_with_default(Account.objects.filter(name='运营资金.人气无忧').aggregate(Sum('balance'))['balance__sum'], 0)
	print "账面剩余资金: {:.2f} - 未结算资金: {:.2f} = 账户留存资金: {:.2f}".format(float(total), float(unaccounted), float(total - unaccounted))

class Sync(object):
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
			if Tmorder.objects.filter(oid=order_id).exists(): #TODO, remove me
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
	def import_cm_express():
		@transaction.atomic
		def __handler(title, line, *args):
			e = Sync.__express_creator(title, line, ["快递公司", "运单号"])
			if not e:
				return
		csv_parser('/tmp/cm.express.csv', None, True, __handler)

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

	@staticmethod
	def import_yz_express():
		Sync.__express_clear(False, '邮政', "邮件号", "邮资", [])

	@staticmethod
	def import_tm_clear():
		__map = (
			#账务类型, 备注, 账户类型, 账户名称, 关联到订单, 从备注获取订单编号
			(r'^交易$', r'^花呗交易号\[\d*\]$', '收入', '天猫营收', '销售额', True, False),
			(r'^交易$', r'^\s*$', '收入', '天猫营收', '销售额', True, False),
			(r'^交易退款$', r'^售后退款-\d*-T200P\d*$', '收入', '天猫营收', '销售额', True, False),
			(r'^交易退款$', r'^花呗-售后退款-\d*-T200P\d*$', '收入', '天猫营收', '销售额', True, False),
			(r'^代扣款-普通账户转账$', r'^代扣返点积分\d{18,}$', '支出', '订单积分', '积分', True, False),
			(r'^代扣款-普通账户转账$', r'^天猫佣金（类目）\{\d{18,}\}扣款$', '支出', '平台佣金', '平台佣金', True, False),
			(r'^代扣款-普通账户转账$', r'^淘宝客佣金退款\[\d{18,}\]$', '支出', '淘宝客佣金', '淘宝客佣金', True, True),
			(r'^代扣款-普通账户转账$', r'^代扣交易退回积分\d*$', '收入', '退回积分', '退回积分', False, False),
			(r'^交易分账$', r'^淘宝客佣金代扣款\[\d*\]$', '支出', '淘宝客佣金', '淘宝客佣金', True, False),
			(r'^交易分账$', r'^分销分账，.*$', '支出', '分销分账', '分销分账', True, False),
			(r'^\s*$', r'^保险承保-卖家版运费险保费收取:淘宝订单号\d{18,}$', '支出', '运费险', '运费险', True, True),
			(r'^服务费$', r'^花呗支付服务费\[\d*\]$', '支出', '服务费', '服务费', True, False),
			(r'^服务费$', r'^信用卡支付服务费\[\d*\]$', '支出', '服务费', '服务费', True, False),
			(r'^提现$', r'^余利宝自动转入$', '资产', '余利宝', '余利宝自动转入', False, False),
			(r'^\s*$', r'^余利宝-基金赎回，转账到支付宝$', '资产', '余利宝', '余利宝赎回', False, False),
			(r'^代扣款-普通账户转账$', r'^代扣款（扣款用途：直通车自动充值-\d*-\d*）$', '资产', '直通车', '直通车自动充值', False, False),
			(r'^提现$', r'^\s*$', '资产', '支付宝.手动周转', '手动周转', False, False),
			(r'^\s*$', r'^天猫保证金-支付-天猫保证金-支付-积分发票违约金$', '支出', '积分发票违约金', '积分发票违约金', False, False),
		)
		@transaction.atomic
		def __handler(title, line, *args):
			org = args[0]
			when, pid, oid, category, receive, pay, remark  = get_column_values(title, line, "入账时间", "支付宝流水号", "商户订单号", "账务类型", "收入（+元）", "支出（-元）", "备注")
			if Tmclear.objects.filter(pid=pid).exists(): return #handled
			t = datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
			when = datetime.now(timezone.get_current_timezone()).replace(*(t.timetuple()[0:6])).replace(microsecond=0)
			if receive != " ": change = Decimal(receive)
			if pay != " ": change = -Decimal(pay)
			handled = False
			for __category, __remark, __account_category, __account_name, __desc, __attach, __retrieve_order_from_remark in __map:
				if not re.compile(__category).match(category): continue
				if not re.compile(__remark).match(remark): continue
				task = None
				if __attach:
					if __retrieve_order_from_remark:
						oid = int(re.compile(r"\d{18,}").search(remark).group())
					else:
						oid = int(re.compile(r"\d{18,}").search(oid).group())
					if not Tmorder.objects.filter(oid=oid).exists():
						print "订单不存在: {}".format(csv_line_2_str(line))
						break
					order = Tmorder.objects.get(oid=oid)
					task = order.task_ptr
				cash = Money.objects.get(name="人民币")
				a = Account.get_or_create(org, cash.item_ptr, "资产", "支付宝.自动结算", None)
				b = Account.get_or_create(org, cash.item_ptr, __account_category, __account_name, None)
				tr = Transaction.add(task, "结算."+__desc, when, a, change, b)
				Tmclear(pid=pid, transaction=tr).save()
				#print "已处理交易: {}".format(csv_line_2_str(line))
				handled=True
				break
			if not handled:
				print "发现未知结算: {}".format(csv_line_2_str(line))
		csv_parser('/tmp/tm.clear.csv', csv_gb18030_2_utf8, True, __handler, Organization.objects.get(name="泰福高腾复专卖店"))

	@staticmethod
	def import_jd_order_clear():
		__map = (
			#费用项, 账户类型, 账户名称, 描述
			(r'^货款$', '收入', '京东营收', '销售额'),
			(r'^代收配送费$', '收入', '运费', '运费'),
			(r'^随单送的京豆$', '支出', '京豆', '京豆'),
			(r'^佣金$', '支出', '佣金', '佣金'),
			(r'^技术服务费$', '支出', '技术服务费', '技术服务费'),
			(r'^代收京麦市场服务费$', '支出', '代收付服务费', '代收付服务费'),
		)
		@transaction.atomic
		def __handler(title, line, *args):
			org = args[0]
			oid, pid, when, category, change  = get_column_values(title, line, "订单编号", "单据编号", "费用结算时间", "费用项", "金额")
			oid = int(re.compile(r"\d+").search(oid).group())
			pid = int(re.compile(r"\d+").search(pid).group())
			if Jdorderclear.objects.filter(pid=pid).exists(): return #handled
			if when == '':
				t = datetime.strptime(get_column_value(title, line, '账单日期'), '%Y%m%d') + timedelta(1)
			else:
				t = datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
			when = datetime.now(timezone.get_current_timezone()).replace(*(t.timetuple()[0:6])).replace(microsecond=0)
			change = Decimal(change)
			handled = False
			for __category, __account_category, __account_name, __desc in __map:
				if not re.compile(__category).match(category): continue
				handled=True
				if not Jdorder.objects.filter(oid=oid).exists():
					task = None
				else:
					order = Jdorder.objects.get(oid=oid)
					task = order.task_ptr
				cash = Money.objects.get(name="人民币")
				a = Account.get_or_create(org, cash.item_ptr, "资产", "订单自动结算", None)
				b = Account.get_or_create(org, cash.item_ptr, __account_category, __account_name, None)
				tr = Transaction.add(task, "结算."+__desc, when, a, change, b)
				Jdorderclear(pid=pid, transaction=tr).save()
				print "已处理交易: {}".format(csv_line_2_str(line))
				break
			if not handled:
				print "发现未知结算: {}".format(csv_line_2_str(line))
		csv_parser('/tmp/jd.clear.order.csv', csv_gb18030_2_utf8, True, __handler, Organization.objects.get(name="为绿厨具专营店"))

	@staticmethod
	def import_jd_wallet_clear():
		__map = (
			#交易备注, 商户订单号, 账户名称, 描述, 追加金额到商户订单号
			(r'^="projectId:\d*_\d*/projectName:POP运费险"$', r'^.*$', '支出', '运费险', '运费险', False),
			(r'^="联盟结算 - \(JDDORS_.*\)\d*@广告联盟\(pc\)"$', r'^.*$', '支出', '广告联盟', '广告联盟', False),
			(r'^="物流结算 - \(JDDORS_.*\)\d*@B商家结算\(新\)"$', r'^.*$', '支出', '物流结算', '物流结算', False),
			(r'^="京东支付货款"$', r'^.*$', '资产', '订单自动结算', '转账', False),
			(r'^="其他支付方式货款"$', r'^.*$', '资产', '订单自动结算', '转账', False),
			(r'^="京东支付费项"$', r'^.*$', '资产', '订单自动结算', '转账', False),
			(r'^="退货金额"$', r'^.*$', '资产', '订单自动结算', '转账', False),
			(r'^="其他支付方式费项"$', r'^.*$', '资产', '订单自动结算', '转账', False),
			(r'^="技术服务费"$', r'^.*$', '资产', '京东快车', '转账', False),
			(r'^="代收付服务费"$', r'^.*$', '支出', '代收付服务费', '代收付服务费', False),
			(r'^="退货抵扣款退回"$', r'^.*$', '支出', '退货抵扣款退回', '退货抵扣款退回', False),
			(r'^.*$', r'^="200000\d{6,6}"$', '资产', '京东钱包', '转账', True), #钱包付款，同一个商户订单号分转账和手续费两条记录，增加金额来区分
			(r'^.*$', r'^="201\d{13,13}"$', '资产', '京东钱包', '转账', False)
		)
		@transaction.atomic
		def __handler(title, line, *args):
			org, when, pid, receive, pay, remark  = get_column_values(title, line, "账户名称", "日期", "商户订单号", "收入金额", "支出金额", "交易备注")
			if Jdwalletclear.objects.filter(pid=pid).exists(): return #handled
			org = org[2:]
			org = Organization.objects.get(name=org[:-1])
			when = re.compile(r"\d{4,4}-\d{2,2}-\d{2,2} \d{2,2}:\d{2,2}:\d{2,2}").search(when).group()
			t = datetime.strptime(when, '%Y-%m-%d %H:%M:%S')
			when = datetime.now(timezone.get_current_timezone()).replace(*(t.timetuple()[0:6])).replace(microsecond=0)
			if receive != "--": change = Decimal(receive)
			if pay != "--": change = -Decimal(pay)
			handled = False
			for __remark, __pid, __account_category, __account_name, __desc, __new_pid in __map:
				if not re.compile(__remark).match(remark): continue
				if not re.compile(__pid).match(pid): continue
				if __new_pid:
					pid += "|" + str(change)
					if Jdwalletclear.objects.filter(pid=pid).exists(): return #handled
				cash = Money.objects.get(name="人民币")
				a = Account.get_or_create(org, cash.item_ptr, "资产", "钱包自动结算", None)
				if __new_pid and change > -50.0:
					b = Account.get_or_create(org, cash.item_ptr, "支出", "付款手续费", None)
				else:
					b = Account.get_or_create(org, cash.item_ptr, __account_category, __account_name, None)
				tr = Transaction.add(None, "结算."+__desc, when, a, change, b)
				Jdwalletclear(pid=pid, transaction=tr).save()
				print "已处理交易: {}".format(csv_line_2_str(line))
				handled=True
				break
			if not handled:
				print "发现未知结算: {}".format(csv_line_2_str(line))
		csv_parser('/tmp/jd.clear.wallet.csv', csv_gb18030_2_utf8, True, __handler)

	@staticmethod
	def import_jd_advertise_clear():
		@transaction.atomic
		def __handler(title, line, *args):
			pid, when, amount = get_column_values(title, line, "序号", "投放日期", "支出（元）")
			pid = int(pid)
			if Jdadvertiseclear.objects.filter(pid=pid).exists(): return #handled
			t = datetime.strptime(when, '%Y-%m-%d')
			when = datetime.now(timezone.get_current_timezone()).replace(*(t.timetuple()[0:6])).replace(microsecond=0)
			amount = Decimal(amount)
			cash = Money.objects.get(name="人民币")
			org = Organization.objects.get(name="为绿厨具专营店")
			a = Account.get_or_create(org, cash.item_ptr, "资产", "京东快车", None)
			b = Account.get_or_create(org, cash.item_ptr, "支出", "京东快车", None)
			tr = Transaction.add(None, "结算.京东快车", when, a, -amount, b)
			Jdadvertiseclear(pid=pid, transaction=tr).save()
			print "已处理交易: {}".format(csv_line_2_str(line))
		csv_parser('/tmp/jd.clear.advertise.csv', None, True, __handler)
