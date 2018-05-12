# -*- coding: utf-8 -*-

from django.db import models

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
