# -*- coding: utf-8 -*-
from django.db import models
from task import *

class ExpressSupplier(models.Model):
	name = models.CharField(max_length=30, unique=True)
	def __str__(self):
		return self.name

class Express(models.Model):
	supplier = models.ForeignKey(ExpressSupplier, verbose_name="快递服务商")
	eid = models.BigIntegerField("快递单号")
	fee = models.DecimalField("运费", default=0, max_digits=8, decimal_places=2)
	clear = models.BooleanField("已结算", default=False)
	task = models.ForeignKey(Task, null=True, blank=True)
	class Meta:
		unique_together = ("supplier", "eid")
	def __str__(self):
		return "{}: {}".format(self.supplier, self.eid)
