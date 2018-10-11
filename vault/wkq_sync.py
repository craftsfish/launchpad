# -*- coding: utf8 -*-
import csv
from ground import *
from django.db import transaction
from .models import *

@transaction.atomic
def import_wkq_transfer():
	def __tm_handler(order_id, amount, when):
		if not Tmorder.objects.filter(oid=order_id).exists():
			print "[警告!!!]天猫订单{}: 未导入".format(order_id)
			return

		order = Tmorder.objects.get(oid=order_id)
		if not order.counterfeit or order.counterfeit.name != "威客圈":
			print "[警告!!!]天猫订单{}: 未标记为威客圈刷单".format(order_id)
			return

		if order.task_ptr.transactions.filter(desc="刷单.结算.威客圈").exists():
			if Transaction.objects.filter(desc="威客圈转账.{}".format(order_id)).exists():
				print "[警告!!!]天猫订单{}: 同时存在结算和转账记录".format(order_id)
			return

		if order.sale != amount:
			print "[警告!!!]天猫订单{}: 订单金额与威客圈付款金额不一致".format(order_id)

		org = Organization.objects.get(name="泰福高腾复专卖店")
		cash = Money.objects.get(name="人民币")
		if Transaction.objects.filter(desc="威客圈转账.{}".format(order_id)).exists():
			t = Transaction.objects.get(desc="威客圈转账.{}".format(order_id))
			splits = t.splits.order_by("account__category")
			if splits[0].account.organization != org:
				t.desc = "转账"
				t.task = order.task_ptr
				t.save()
				s = splits[1]
				s.account = Account.get_or_create(splits[1].account.organization, cash.item_ptr, "资产", "应收账款.{}".format(org), None)
				s.save()
				a = Account.get_or_create(org, cash.item_ptr, "负债", "应付账款.{}".format(splits[1].account.organization), None)
				b = Account.get(org, cash.item_ptr, "支出", "威客圈刷单", None)
				Transaction.add(order.task_ptr, "刷单.结算.威客圈", when, a, amount, b)
				print "[警告!!!]天猫订单{}: 增加威客圈换主体记录".format(order_id)
			else:
				t.desc = "刷单.结算.威客圈"
				t.task = order.task_ptr
				t.save()
				print "[警告!!!]天猫订单{}: 增加威客圈关联任务记录".format(order_id)
		else: #没有原始转账记录的订单，默认从招行支付
			a = Account.get(org.root(), cash.item_ptr, "资产", "借记卡-招行6482", None)
			b = Account.get(org, cash.item_ptr, "支出", "威客圈刷单", None)
			Transaction.add(order.task_ptr, "刷单.结算.威客圈", when, a, -amount, b)
			print "[警告!!!]天猫订单{}: 增加威客圈转账记录".format(order_id)

	def __jd_handler(order_id, amount, when):
		print "[警告!!!]京东订单{}: 暂不支持".format(order_id)

	def __handler(title, line, *args):
		oid, amount, status, when = get_column_values(title, line, "订单编号", "转账金额", '转账状态', '转账时间')
		if status != '转账成功':
			return
		t = datetime.strptime(when, "%Y/%m/%d %H:%M:%S")
		when = datetime.now(timezone.get_current_timezone()).replace(*(t.timetuple()[0:6])).replace(microsecond=0)
		amount = Decimal(amount)
		order_id = int(oid)
		if is_tm_order(oid):
			__tm_handler(order_id, amount, when)
		elif is_jd_order(oid):
			__jd_handler(order_id, amount, when)
		else:
			print "[警告!!!]订单{}: 无法识别所属平台".format(order_id)

	#main
	csv_parser('/tmp/wkq.transfer.csv', None, True, __handler)

@transaction.atomic
def import_wkq_detail():
	def __handler(title, line, *args):
		pid, kind, amount_1, amount_2, when, desc = get_column_values(title, line, '消费ID', '类型', '消费存款', '消费发布点', '操作时间', '备注')
		if kind in ['购买发布点', '充值']:
			return
		t = datetime.strptime(when, "%Y/%m/%d %H:%M:%S")
		when = datetime.now(timezone.get_current_timezone()).replace(*(t.timetuple()[0:6])).replace(microsecond=0)
		amount_1 = Decimal(amount_1)
		amount_2 = Decimal(amount_2)
		if not Transaction.objects.filter(desc=pid).filter(time=when).exists():
			org = Organization.objects.get(name="泰福高腾复专卖店")
			cash = Money.objects.get(name="人民币")
			a = Account.get(org.root(), cash.item_ptr, "资产", "运营资金.威客圈", None)
			b = Account.get(org, cash.item_ptr, "支出", "威客圈刷单", None)
			Transaction.add(None, pid, when, a, amount_1+amount_2, b)
			print "增加威客圈流水记录: {} | {}, {}, {}".format(when, pid, kind, desc)

	#main
	csv_parser('/tmp/wkq.detail.csv', None, True, __handler)

@transaction.atomic
def import_wkq_request():
	__bank_mapping = (
		#威客圈银行名称, 京东银行名称
		('中国工商银行', '中国工商银行'),
		('中国农业银行', '中国农业银行'),
		('中国银行', '中国银行'),
		('中国建设银行', '中国建设银行'),
		('中国邮政储蓄银行', '中国邮政储蓄银行'),
		('', '广东发展银行'),
		('', '中国光大银行'),
		('交通银行', '交通银行'),
		('', '招商银行'),
		('兴业银行', '兴业银行'),
		('平安银行', '平安银行（深发展）'),
		('中信银行', '中信银行'),
		('', '中国民生银行'),
		('上海浦东发展银行', '上海浦东发展银行'),
		('华夏银行', '华夏银行'),
		('', '北京银行'),
		('', '上海银行'),
		('', '宁波银行'),
		('', '广州银行'),
		('', '杭州银行'),
	)
	def __handler(title, line, *args):
		jd_script = args[0]
		zh_script = args[1]
		account, name, amount, remark, bank = get_column_values(title, line, '收款账户列', '收款户名列', '转账金额列', '备注列', '收款银行列')
		#print "[威客圈][等待转账][处理中...] {}, {}, {}, {}, {}".format(bank, account, name, amount, remark)
		using_jd_wallet = False
		for wkq_bank, jd_bank in __bank_mapping:
			if wkq_bank == bank:
				using_jd_wallet = True
				bank = jd_bank
				break
		if not using_jd_wallet:
			if not len(zh_script):
				zh_script.append(title)
			zh_script.append(line)
			print "京东钱包当前不支持 {} 转账".format(bank)
		else:
			jd_script.append([len(jd_script)+1, account, bank, name, amount, '对私', '借记卡', '', '', '', '', remark, '', ''])

		org = Organization.objects.get(name="为绿厨具专营店")
		account_name = '京东钱包'
		if not using_jd_wallet:
			account_name = '借记卡-招行6482'
		cash = Money.objects.get(name="人民币")
		a = Account.get_or_create(org, cash.item_ptr, "资产", account_name, None)
		b = Account.get_or_create(org, cash.item_ptr, "支出", "威客圈刷单", None)
		Transaction.add(None, "威客圈转账.{}".format(remark), now(), a, -Decimal(amount), b)

	#main
	jd_script = []
	zh_script = []
	csv_parser('/tmp/wkq.request.csv', None, True, __handler, jd_script, zh_script)
	with open("/tmp/jd_wallet_{}.csv".format(now()), "wb") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(['单笔序号','收款方银行账号','银行类型','真实姓名','付款金额(元)','账户属性','账户类型','开户地区','开户城市','支行名称','联行号','付款说明','收款人手机号','所属机构'])
		for l in jd_script:
			writer.writerow(l)
	with open("/tmp/zh_transfer.csv", "wb") as csvfile:
		writer = csv.writer(csvfile)
		for l in zh_script:
			writer.writerow(l)
