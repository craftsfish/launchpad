# -*- coding: utf-8 -*-
from django.db import models

class Repository(models.Model):
	name = models.CharField(max_length=30, unique=True)

	def __str__(self):
		return self.name
