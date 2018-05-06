# -*- coding: utf-8 -*-

from django.db import models

class Task(models.Model):
	desc = models.CharField(max_length=120)

	def __str__(self):
		return self.desc

	def delete(self, *args, **kwargs):
		for t in self.transactions.all():
			t.delete()
		super(Task, self).delete(*args, **kwargs)
