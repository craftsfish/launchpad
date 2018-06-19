# -*- coding: utf-8 -*-
from django.db import models

class Counterfeit(models.Model):
	name = models.CharField("平台", max_length=30, unique=True)
	delivery = models.BooleanField("真实发货")
	recall = models.BooleanField("实物回收")

	def __str__(self):
		s = self.name
		if self.delivery:
			s += " | 支持" + self.__class__._meta.get_field('delivery').verbose_name
		if self.recall:
			s += " | 支持" + self.__class__._meta.get_field('recall').verbose_name
		return s
