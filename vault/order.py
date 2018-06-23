# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from counterfeit import *
from repository import *

class Order(models.Model):
	"""
	[订单]
	一个订单可以包含多条订购记录(invoice)，采用的是平台的商品编号，并且是一个无序的列表，同一平台商品可以出现多次。
	系统内部对订单内的所有invoice按照平台编号，购买数量进行排序。
	一个平台商品可以对应物理上的多个商品，内部通过构建相应的映射表，来描述两者之间的关系。
	每个映射有时间戳表示生效时间，这样的设计允许平台商品在不同的时间段映射不同的物理商品组合。
	系统内部标识一个具体的物理出货记录时，transaction的desc属性格式为{invoice排序号}.出货.{平台编号}.{商品名称}
	TODO: 这里的商品名称是否必要，因为每个transacton对应的交易标的已经包含了该信息？

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
	刷单.结算 | 刷单.结算 | (刷单的费用，实际订单费用)
	刷单.佣金 | 刷单.拥挤 | (刷单的费用，佣金)
	退货 | 退货 | (正常退货，京东平台退货不反应在订单状态内，所以直接记录为一条收货记录，天猫则记录为一条换仓记录)
	换货.收货 | 换货.收货 | (订单换货)
	换货.发货 | 换货.发货 | (订单换货)
	结算 | 结算 | (订单费用结算)
	返现 | 返现 | (给客户返利)

	[内部处理]
	为每一种transaction设计处理相应的handler，各自负责对于的transaction的增加，删除，更新
	"""
	time = models.DateTimeField(default=timezone.now)
	repository = models.ForeignKey(Repository, null=True, blank=True, related_name="%(app_label)s_%(class)s_order_set", related_query_name="%(app_label)s_%(class)s", verbose_name="发货仓库")
	sale = models.DecimalField(max_digits=20, decimal_places=2, default=0)
	counterfeit = models.ForeignKey(Counterfeit, verbose_name="刷单平台", null=True, blank=True)
	delivery = models.BooleanField("真实发货", default=False)
	recall = models.BooleanField("实物回收", default=False)
	recall_repository = models.ForeignKey(Repository, null=True, blank=True, related_name="%(app_label)s_%(class)s_recall_order_set", related_query_name="%(app_label)s_%(class)s_recall", verbose_name="刷单回收仓库")

	class Meta:
		abstract = True
