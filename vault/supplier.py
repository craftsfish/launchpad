# -*- coding: utf-8 -*-

from django.db import models

class Supplier(models.Model):
	name = models.CharField(max_length=30, unique=True)
	period = models.IntegerField(default=15) #供货周期

	def __str__(self):
		return self.name
