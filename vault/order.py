# -*- coding: utf-8 -*-
from django.db import models
from django.db import transaction
from django.utils import timezone
from counterfeit import *
from repository import *
from task import *
import re

class Order(models.Model):
	"""
	[订单]
	一个订单是一个Task，设计上应该继承Task模型。TODO: 能否迁移?
	一个订单可以包含多条订购记录(invoice)，采用的是平台的商品编号，并且是一个无序的列表，同一平台商品可以出现多次。
	订单内的每个invoice有各自独立的状态，整个订单有一个综合状态。
	系统内部对订单的所有invoice按照平台编号，购买数量进行排序。
	invoice永远存在，有以下几种状态 {
		等待出库: (负债.应发, -1 | 支出.出货, +1)
		已经出库: (资产.完好, -1 | 支出.出货, +1)
		订购取消: (支出.出库, +1 | 支出.出货, +1)
	}TODO: 目前还不支持，优先级高，影响整个order的更新设计。
	一个平台商品可以对应物理上的多个商品，内部通过构建相应的映射表，来描述两者之间的关系。
	每个映射有时间戳表示生效时间，这样的设计允许平台商品在不同的时间段映射不同的物理商品组合。
	系统内部标识一个具体的物理出货记录时，transaction的desc属性格式为{invoice排序号}.出货.{平台编号}.{商品名称}
	TODO: 这里的商品名称是否必要，因为每个transacton对应的交易标的已经包含了该信息？
	TODO: transaction的desc的格式修改为出货.{invoice排序号}.{平台编号}，这样方便生成订单内的其他关联交易。

	[刷单]
	1: 空包
	2: 发事先约定的物品
	3: 真实发货，货物赠送
	4: 真实发货，刷收收到后寄回

	[订单内部描述]
	出货 | {invoice排序号}.出货.{平台编号}.{商品名称} | (正常订单出货流程，根据订单状态，反应真实的仓库情况，应发/已发)
	刷单.回收 | {invoice排序号}.刷单.回收.{平台编号}.{商品名称} |(不需要真实发货的刷单，立刻通过此条目中和正常出货的效果)
	刷单.应退 | {invoice排序号}.刷单.应收.{平台编号}.{商品名称} | (需要回收实物的刷单，通过此条目记录下应收明细)
	刷单.入库 | {invoice排序号}.刷单.入库.{平台编号}.{商品名称} | (需回收实物的刷单，通过此条目记录收货详情)
	刷单.发货 | 刷单.发货 | (根据具体情况的不同，刷单需要发出的货物，比如洗衣粉，肥皂，盐等)
	刷单.结算 | 刷单.结算 | (刷单的费用，实际订单费用+佣金)
	退货 | 退货 | (正常退货，对应的invoice状态为完成，则记录为一条收货记录。状态为删除或者取消则记录为一条换仓记录。TODO：这个规则目前还没有应用)
	换货.收货 | 换货.收货 | (订单换货)
	换货.发货 | 换货.发货 | (订单换货)
	结算 | 结算 | (订单费用结算)
	返现 | 返现 | (给客户返利)

	[内部处理]
	为每一种transaction设计处理相应的handler，各自负责对于的transaction的增加，删除，更新
	冲突处理原则: 自动生成的数据采用激进策略，强制同步，人工输入的数据提示错误，由管理员手动调整。
	"""
	time = models.DateTimeField(default=timezone.now)
	repository = models.ForeignKey(Repository, null=True, blank=True, related_name="%(app_label)s_%(class)s_order_set", related_query_name="%(app_label)s_%(class)s", verbose_name="发货仓库")
	sale = models.DecimalField(max_digits=20, decimal_places=2, default=0)

	#以下属于仅适用于刷单
	counterfeit = models.ForeignKey(Counterfeit, verbose_name="刷单平台", null=True, blank=True)
	counterfeit_auto_clear = models.BooleanField("刷单自动结算", default=False)
	delivery = models.BooleanField("真实发货", default=False)
	recall = models.BooleanField("实物回收", default=False)
	recall_repository = models.ForeignKey(Repository, null=True, blank=True, related_name="%(app_label)s_%(class)s_recall_order_set", related_query_name="%(app_label)s_%(class)s_recall", verbose_name="刷单回收仓库")

	class Meta:
		abstract = True

	def create_or_update_invoice_shipment(self, organization, invoice_id, platform_commodity_id, commodities, quantity, delivery):
		prefix = "{}.出货.".format(invoice_id)
		task = self.task_ptr
		repository = self.repository
		dest = ("支出", "出货", repository)
		if delivery == DeliveryStatus.delivered:
			source = ("资产", "完好", repository)
			quantity = -quantity
		elif delivery == DeliveryStatus.inbook:
			source = ("负债", "应发", repository)
		else:
			source = ("支出", "出货", repository)
			quantity = -quantity

		transaction = task.transactions.filter(desc__startswith=prefix).first()
		if transaction: #update
			splits = transaction.splits.order_by("account__category", "change")
			a = splits[0].account
			b = Account.get_or_create(organization, a.item, *source)
			if a.id == b.id:
				return

			for i in task.transactions.filter(desc__startswith=prefix):
				splits = i.splits.order_by("account__category", "change")
				s = splits[0]
				s.account = Account.get_or_create(organization, s.account.item, *source)
				s.change = quantity
				s.save()
				if a.repository.id != repository.id:
					s = splits[1]
					s.account = Account.get_or_create(organization, a.item, *dest)
					s.save()
		else: #create
			for c in commodities:
				Transaction.add_raw(task, "{}.出货.{}.{}".format(invoice_id, platform_commodity_id, c.name),
					self.time, organization, c.item_ptr,
					source, quantity, dest)

	@staticmethod
	def fake_recall_create(task): #刷单.回收
		for i in task.transactions.filter(desc__contains=".出货.").order_by("id"):
			p = re.compile(r"\d*").match(i.desc).end()
			a = i.desc[:p]
			b = i.desc[p+4:]
			args = []
			for s in i.splits.order_by("account__category"):
				args.append(s.account)
				args.append(-s.change)
			Transaction.add(task, "{}.刷单.回收.{}".format(a, b), i.time, *args)

	def fake_recall_update(self): #刷单.回收
		task = self.task_ptr
		for i in task.transactions.filter(desc__contains=".出货.").order_by("id"):
			p = re.compile(r"\d*").match(i.desc).end()
			a = i.desc[:p]
			b = i.desc[p+4:]
			j = task.transactions.get(desc="{}.刷单.回收.{}".format(a, b))
			f = j.splits.order_by("account__category", "-change")
			t = i.splits.order_by("account__category", "-change")
			for k, s in enumerate(f):
				s.account = t[k].account
				s.change = -t[k].change
				s.save()

	def update(self):
		task = self.task_ptr
		first_shipment = task.transactions.filter(desc__startswith="1.出货.").first()
		if not first_shipment:
			return
		shipout_split = first_shipment.splits.filter(account__category=Account.str2category("支出")).get(change__gt=0)
		original_repository = shipout_split.account.repository
		organization = shipout_split.account.organization

		#刷单处理
		if not self.counterfeit:
			return

		#刷单.回收
		if not self.counterfeit.delivery:
			if not task.transactions.filter(desc__contains="刷单.回收").exists():
				Order.fake_recall_create(task)
			else:
				self.fake_recall_update()
		else:
			task.delete_transactions_contains_desc("刷单.回收")

		#刷单.结算.陆凤
		if self.counterfeit.name != "陆凤":
			if task.transactions.filter(desc="刷单.结算.陆凤").exists():
				print "[Error]{}.{} 没有标记为陆凤刷单，有陆凤刷单结算交易，请确认后手动调整".format(self, self.oid)

		#刷单.结算.微信
		if self.counterfeit.name == "微信":
			if self.counterfeit_auto_clear and not task.transactions.filter(desc="刷单.结算.微信").exists():
				cash = Money.objects.get(name="人民币")
				a = Account.get(organization, cash.item_ptr, "支出", "{}刷单".format(self.counterfeit), None)
				b = Account.get(organization.root(), cash.item_ptr, "资产", "运营资金.微信", None)
				Transaction.add(task, "刷单.结算.微信", timezone.now(), a, self.sale, b)
		else:
			if task.transactions.filter(desc="刷单.结算.微信").exists():
				print "[Error]{}.{} 没有标记为微信刷单，有微信刷单结算交易，请确认后手动调整".format(self, self.oid)

		#退货
		#TODO: 根据对应的invoice状态处理
