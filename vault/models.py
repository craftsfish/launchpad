# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Organization(models.Model):
	name = models.CharField(max_length=30)
	parent = models.ForeignKey('self', verbose_name="上级", null=True, blank=True, related_name="children")

	def __str__(self):
		return self.name

class Supplier(models.Model):
	name = models.CharField(max_length=30, unique=True)

	def __str__(self):
		return self.name

class Item(models.Model):
	class Meta:
		unique_together = ("supplier", "name")
		ordering = ['supplier__id', 'name']

	name = models.CharField("品名", max_length=30)
	supplier = models.ForeignKey(Supplier, verbose_name="供应商")
	value = models.DecimalField("价值", default=0, max_digits=8, decimal_places=2)

	def __str__(self):
		return self.name
