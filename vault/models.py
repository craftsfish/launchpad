# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Organization(models.Model):
	name = models.CharField(max_length=30)
	parent = models.ForeignKey('self', verbose_name="上级", null=True, blank=True, related_name="children")

	def __str__(self):
		return self.name
