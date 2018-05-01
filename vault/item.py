# -*- coding: utf-8 -*-

from django.db import models
from supplier import *

class Item(models.Model):
	class Meta:
		unique_together = ("supplier", "name")
		ordering = ['supplier__id', 'name']

	name = models.CharField("品名", max_length=30, unique=True)
	supplier = models.ForeignKey(Supplier, verbose_name="供应商")
	value = models.DecimalField("价值", default=0, max_digits=8, decimal_places=2)

	def __str__(self):
		return self.name
