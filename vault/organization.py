# -*- coding: utf-8 -*-
import uuid
from django.db import models

class Organization(models.Model):
	uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
	name = models.CharField(max_length=30)
	parent = models.ForeignKey('self', verbose_name="上级", null=True, blank=True, related_name="children")

	def __str__(self):
		return self.name

	def descendants(self):
		result = [self]
		i = 0
		while i < len(result):
			for c in result[i].children.all():
				result.append(c)
			i += 1
		result.pop(0)
		return result

	def root(self):
		r = self
		while r.parent:
			r = r.parent
		return r
