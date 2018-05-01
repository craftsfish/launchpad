# -*- coding: utf-8 -*-

from django.db import models
from item import *

class Jdcommodity(models.Model):
	id = models.BigIntegerField("京东商品编码", primary_key=True)
	items = models.ManyToManyField(Item, verbose_name="物品")
	since = models.DateTimeField("生效时间")

	def __str__(self):
		result = str(self.since)
		for i in self.items.all():
			result += ", " + i.name
		return result
