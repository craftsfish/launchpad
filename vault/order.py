# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from counterfeit import *
from repository import *

class Order(models.Model):
	time = models.DateTimeField(default=timezone.now)
	repository = models.ForeignKey(Repository, null=True, blank=True, related_name="%(app_label)s_%(class)s_order_set", related_query_name="%(app_label)s_%(class)s", verbose_name="发货仓库")
	sale = models.DecimalField(max_digits=20, decimal_places=2, default=0)
	counterfeit = models.ForeignKey(Counterfeit, verbose_name="刷单平台", null=True, blank=True)
	delivery = models.BooleanField("真实发货", default=False)
	recall = models.BooleanField("实物回收", default=False)
	recall_repository = models.ForeignKey(Repository, null=True, blank=True, related_name="%(app_label)s_%(class)s_recall_order_set", related_query_name="%(app_label)s_%(class)s_recall", verbose_name="刷单回收仓库")

	class Meta:
		abstract = True
