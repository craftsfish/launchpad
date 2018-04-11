# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Organization(models.Model):
	name = models.CharField(max_length=30)
	parent = models.ForeignKey('self', verbose_name="上级", null=True, blank=True, related_name="children")

	def __str__(self):
		result = self.name
		parent = self.parent
		while parent:
			result = parent.name + "." + result
			parent = parent.parent
		return result

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

class Account(models.Model):
	name = models.CharField("名称", max_length=30, null=True, blank=True)
	balance = models.DecimalField("余额", default=0, max_digits=20, decimal_places=2)
	organization = models.ForeignKey(Organization, verbose_name="组织")
	item = models.ForeignKey(Item, verbose_name="物资")
	ACCOUNT_CATEGORY_CHOICES = (
		(0, "资产"),
		(1, "负债"),
		(2, "收入"),
		(3, "支出"),
		(4, "净资产"),
	)
	category = models.IntegerField(choices=ACCOUNT_CATEGORY_CHOICES, default=0)

	def __str__(self):
		return "{}.{}.{}.{}".format(str(self.organization), self.item.name, self.get_category_display(), self.name)
