# -*- coding: utf-8 -*-
from django.db import models

class Counterfeit(models.Model):
	"""
	Platform used to make counterfeit orders of various kinds of e-commerce platform.
	"""
	name = models.CharField("平台", max_length=30, unique=True)
	delivery = models.BooleanField("真实发货") #whether the real delivery of goods in order is supported by this platform
	recall = models.BooleanField("实物回收") #whether the recall of real delivered goods is supported by this platform

	def __str__(self):
		s = self.name
		if self.delivery:
			s += " | 支持" + self.__class__._meta.get_field('delivery').verbose_name
		if self.recall:
			s += " | 支持" + self.__class__._meta.get_field('recall').verbose_name
		return s
