# -*- coding: utf8 -*-
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django import forms
from .models import *

class EmptyForm(forms.Form):
	pass

class Turbine:
	@staticmethod
	def get_shipping_out_information(commodity, repository, span):
		r = []
		speed = 0
		active = 0
		decay = 0.7
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for i in range(span):
			q = Split.objects.filter(account__item=commodity).filter(account__repository=repository).filter(account__name="出货")
			q = q.filter(transaction__time__gte=(e-timedelta(1))).filter(transaction__time__lt=e)
			v = q.aggregate(Sum('change'))['change__sum']
			if v: v = int(v)
			else: v = 0
			r.append(v)
			speed += decay ** i * (1 - decay) * v
			if v: active += 1
			e -= timedelta(1)
		speed = speed * active / span
		r.append(speed)
		return r

	@staticmethod
	def get_replenish_information(commodity, repository, speed, threshold):
		inventory = Account.objects.filter(item=commodity).filter(repository=repository).filter(name__in=["完好", "应收"]).aggregate(Sum('balance'))['balance__sum']
		if inventory: inventory = int(inventory)
		else: inventory = 0
		if speed <= 0:
			return [8888, -inventory]
		else:
			return [inventory/speed, speed * threshold - inventory]

	@staticmethod
	def replenish():
		l = []
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for c in Split.objects.filter(account__name="出货").filter(transaction__time__gte=(e-timedelta(28))).filter(transaction__time__lt=e).values_list('account__item', flat=True).distinct():
			if Commodity.objects.filter(pk=c).exists():
				c = Commodity.objects.get(pk=c)
				c.detail = []
				need_refill = False
				for r in Repository.objects.order_by("id"):
					shipping = Turbine.get_shipping_out_information(c, r, 10)
					speed = shipping[len(shipping)-1]
					level, refill = Turbine.get_replenish_information(c, r, speed, 30)
					if refill > 0:
						need_refill = True
					if refill != 0:
						c.detail.append([r, level, refill])
				if need_refill:
					l.append(c)
		def __key(c):
			if c.supplier:
				return "{}-{}".format(c.supplier.id, c.name)
			else:
				return "None-{}".format(c.name)
		l = sorted(l, key=__key)
		for c in l:
			for repo, level, refill in c.detail:
				print "{}: {} | 库存天数: {} | 补仓数量: {}".format(c, repo, level, refill)
		return l

	@staticmethod
	def calibration():
		@transaction.atomic
		def __csv_handler(orgs, l):
			r = Repository.objects.get(name=get_column_value(title, l, "仓库"))
			s = get_column_value(title, l, "状态")
			c = Commodity.objects.get(name=get_column_value(title, l, "品名"))
			q = int(get_column_value(title, l, "库存"))
			v = Account.objects.filter(item=c).filter(repository=r).filter(name=s).aggregate(Sum('balance'))['balance__sum']
			if v: v = int(v)
			else: v = 0
			diff = q - v
			if diff != 0:
				t = Task(desc="盘库")
				t.save()
				n = len(orgs)
				for o in orgs:
					__diff = diff / n
					diff -= __diff
					n -= 1
					if __diff > 0: #surplus
						Transaction.add_raw(t, "盘盈", timezone.now(), o, c.item_ptr, ("资产", s, r), __diff, ("收入", "盘盈", r))
					elif __diff < 0:
						Transaction.add_raw(t, "盘亏", timezone.now(), o, c.item_ptr, ("资产", s, r), __diff, ("支出", "盘亏", r))

		with open('/tmp/calibration.csv', 'rb') as csvfile:
			orgs = Organization.objects.filter(parent=None).exclude(name="个人")
			reader = csv.reader((csvfile))
			title = reader.next()
			for l in reader:
				__csv_handler(orgs, l)

	@staticmethod
	def add_account():
		info = (
			("南京为绿电子科技有限公司", "人民币", "资产", None, "应收账款"),
		)
		for o, i, c, r, n in info:
			with transaction.atomic():
				o = Organization.objects.get(name=o)
				i = Item.objects.get(name=i)
				if r:
					r = Repository.objects.get(name=r)
				Account.get(o, i, c, n, r)

	@staticmethod
	def import_wechat(): #TODO: remove me
		@transaction.atomic
		def __csv_handler(l):
			q, id, n = l
			q = Decimal(q)
			if n == "为绿":
				org = Organization.objects.get(name="为绿厨具专营店")
				o = Jdorder.objects.get(oid=id)
				if not o.task_ptr.transactions.filter(desc="微信刷单.结算").exists():
					query = o.task_ptr.transactions.filter(desc__contains="出货")
					if not query.exists():
						print "订单未导入 : {}".format(id)
						return
					t = query[0].time
					cash = Money.objects.get(name="人民币")
					a = Account.get(org.root(), cash.item_ptr, "负债", "应付账款", None)
					b = Account.get(org, cash.item_ptr, "支出", "刷单", None)
					Transaction.add(o.task_ptr, "微信刷单.结算", t, a, q, b)
					_org = Organization.objects.get(name="个人")
					a = Account.get(_org, cash.item_ptr, "资产", "应收账款-为绿", None)
					b = Account.get(_org, cash.item_ptr, "资产", "刷单资金", None)
					Transaction.add(None, "微信刷单", t, a, q, b)
			elif n == "腾复":
				org = Organization.objects.get(name="泰福高腾复专卖店")
				o = Tmorder.objects.get(oid=id)
				if not o.task_ptr.transactions.filter(desc="微信刷单.结算").exists():
					query = o.task_ptr.transactions.filter(desc__contains="出货")
					if not query.exists():
						print "订单未导入 : {}".format(id)
						return
					t = query[0].time
					cash = Money.objects.get(name="人民币")
					a = Account.get(org.root(), cash.item_ptr, "负债", "应付账款", None)
					b = Account.get(org, cash.item_ptr, "支出", "刷单", None)
					Transaction.add(o.task_ptr, "微信刷单.结算", t, a, q, b)
					_org = Organization.objects.get(name="个人")
					a = Account.get(_org, cash.item_ptr, "资产", "应收账款-腾复", None)
					b = Account.get(_org, cash.item_ptr, "资产", "刷单资金", None)
					Transaction.add(None, "微信刷单", t, a, q, b)
			else:
				print "未知组织"


		with open('/tmp/wechat.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			for l in reader:
				__csv_handler(l)
