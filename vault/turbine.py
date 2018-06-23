# -*- coding: utf8 -*-
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django import forms
from .models import *
from wallet import *
from counterfeit import *

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
	def replenish(supplier):
		l = []
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for c in Split.objects.filter(account__name="出货").filter(transaction__time__gte=(e-timedelta(28))).filter(transaction__time__lt=e).values_list('account__item', flat=True).distinct():
			if Commodity.objects.filter(pk=c).filter(supplier=supplier).filter(inproduction=True).exists():
				c = Commodity.objects.get(pk=c)
				threshold = 15
				if c.supplier:
					threshold = c.supplier.period
				threshold += 10
				c.detail = []
				need_refill = False
				for r in Repository.objects.order_by("id"):
					shipping = Turbine.get_shipping_out_information(c, r, 10)
					speed = shipping[len(shipping)-1]
					level, refill = Turbine.get_replenish_information(c, r, speed, threshold)
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
	def calibration_commodity(task, commodity, repository, status, quantity, organizations):
		v = Account.objects.filter(item=commodity).filter(repository=repository).filter(name=status).aggregate(Sum('balance'))['balance__sum']
		if v: v = int(v)
		else: v = 0
		diff = quantity - v
		commodity.calibration = timezone.now()
		commodity.save()
		if diff != 0:
			if task == None:
				task = Task(desc="盘库")
				task.save()
			n = len(organizations)
			for o in organizations:
				__diff = diff / n
				diff -= __diff
				n -= 1
				if __diff > 0: #surplus
					Transaction.add_raw(task, "盘盈", timezone.now(), o, commodity.item_ptr, ("资产", status, repository), __diff, ("收入", "盘盈", repository))
				elif __diff < 0:
					Transaction.add_raw(task, "盘亏", timezone.now(), o, commodity.item_ptr, ("资产", status, repository), __diff, ("支出", "盘亏", repository))
		return task

	@staticmethod
	def calibration_storage():
		@transaction.atomic
		def __csv_handler(orgs, l):
			r = Repository.objects.get(name=get_column_value(title, l, "仓库"))
			s = get_column_value(title, l, "状态")
			c = Commodity.objects.get(name=get_column_value(title, l, "品名"))
			q = int(get_column_value(title, l, "库存"))
			Turbine.calibration_commodity(None, c, r, s, q, orgs)

		with open('/tmp/storage.csv', 'rb') as csvfile:
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
				Account.get_or_create(o, i, c, n, r)

	@staticmethod
	def dump_storage():
		@transaction.atomic
		def __handler(result, repository, status, commodity):
			v = Account.objects.filter(item=commodity).filter(repository=r).filter(name=status).aggregate(Sum('balance'))['balance__sum']
			if v: v = int(v)
			else: v = 0
			result.append([repository, status, commodity, v])

		with transaction.atomic():
			commodities = Commodity.objects.exclude(supplier=Supplier.objects.get(name="耗材")).order_by("supplier", "name")
			repositories = Repository.objects.all()

		result = []
		for r in repositories:
			for i, s in Itemstatus.choices:
				for c in commodities:
					__handler(result, r, s, c)

		with open("/tmp/storage.csv", "wb") as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(["仓库", "状态", "品名", "库存"])
			for r in result:
				writer.writerow(r)

	@staticmethod
	def update_calibration_window():
		with transaction.atomic():
			c = Commodity.objects.get(name="虚拟物品")
			t = datetime.now(timezone.get_current_timezone()) + timedelta(1)
			t = t.replace(hour=9, minute=0, second=0, microsecond=0)
			c.calibration = t
			c.save()
			print "设置盘库的有效截至日期为: {}".format(t)

	@staticmethod
	@transaction.atomic
	def build():
		wallets = ["借记卡-交行0400", "借记卡-华夏3536", "借记卡-建行6394", "借记卡-招行6482", "借记卡-民生7158", "运营资金.微信", "运营资金.支付宝", "信用卡-建行9662", "信用卡-招行3573"]
		cash = Money.objects.get(name="人民币")
		for w in wallets:
			Wallet.objects.get_or_create(name=w)
			for o in Organization.objects.filter(parent=None):
				if w.find("信用卡") == 0:
					Account.get_or_create(o, cash.item_ptr, "负债", w, None)
				else:
					Account.get_or_create(o, cash.item_ptr, "资产", w, None)

		for p in ["淘宝", "天猫", "京东"]:
			Platform.objects.get_or_create(name=p)

		counterfeits = (
			#平台, 真实发货, 实物回收
			("陆凤", False, False),
			("微信", False, False),
			("买家秀", True, True),
		)
		for n, d, r in counterfeits:
			Counterfeit.objects.get_or_create(name=n, delivery=d, recall=r)

	@staticmethod
	def wechat_fake_clear(organization, task, time, bill):
		cash = Money.objects.get(name="人民币")
		a = Account.get(organization, cash.item_ptr, "支出", "微信刷单", None)
		b = Account.get(organization.root(), cash.item_ptr, "资产", "运营资金.微信", None)
		Transaction.add(task, "微信刷单.结算", time, a, bill, b)

	@staticmethod
	def wechat_fake_migration():
		@transaction.atomic
		def __handler(task_id):
			print task_id

		with transaction.atomic():
			tasks = Transaction.objects.filter(desc__startswith="微信刷单").order_by("task").exclude(task=None).values_list('task', flat=True).distinct("task")

		for t in tasks:
			__handler(t)
