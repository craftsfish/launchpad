# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils import timezone
from django.core.urlresolvers import reverse

# Create your models here.
class Supplier(models.Model):
	name = models.CharField(max_length=30, unique=True)

	def __str__(self):
		return self.name

class Commodity(models.Model):
	name = models.CharField(max_length=30, unique=True)
	supplier = models.ForeignKey(Supplier)

	#for buy
	bvalue = models.IntegerField(default=0)
	bvat = models.IntegerField(default=0)

	#for purchase
	pvalue = models.IntegerField(default=0)
	pvat = models.IntegerField(default=0)

	def __str__(self):
		return self.name

class Account(models.Model):
	class Meta:
		ordering = ['id']

	name = models.CharField("名称", max_length=30, unique=True)
	balance = models.BigIntegerField(default=0)
	ancestors = models.ManyToManyField('self', through='Path', through_fields=('descendant', 'ancestor'), symmetrical=False, related_name="descendants")

	def __str__(self):
		result = "/"
		for p in Path.objects.all().filter(descendant=self.id).order_by('-height')[1:]:
			result += Account.objects.get(pk=p.ancestor.id).name
			if p.height != 0:
				result += "/"
		return result

	def get_absolute_url(self):
		return reverse('account_detail', kwargs={'pk': self.pk})

	def parent(self):
		p = Path.objects.all().filter(descendant=self.id).filter(height=1)
		if len(p) != 1:
			return None
		return p[0].ancestor

	def set_parent(self, parent):
		d = self.descendants.all().values_list('id', flat=True)
		if self.parent(): #remove obsolete paths
			a = self.ancestors.all().exclude(id=self.id).values_list('id', flat=True)
			Path.objects.all().filter(ancestor__in=a).filter(descendant__in=d).delete()

		cur = self
		while parent:
			for _d in d:
				h = Path.objects.all().filter(ancestor=cur.id).filter(descendant=_d).values_list("height", flat=True)[0]
				Path(ancestor=parent, descendant=Account.objects.get(id=_d), height=h+1).save()
			cur = parent
			parent = cur.parent()

	def children(self):
		ids = Path.objects.all().filter(ancestor=self.id).filter(height=1).values_list("descendant", flat=True)
		return Account.objects.filter(id__in=ids)

	def is_leaf(self):
		return len(self.children()) == 0

	def delete_paths2ancestor(self):
		self.paths2ancestor.all().delete()

	@staticmethod
	def root():
		return Account.objects.get(name="帐")

class Path(models.Model): 
	class Meta:
		unique_together = ("ancestor", "descendant")

	ancestor = models.ForeignKey(Account, related_name='paths2descendant')
	descendant = models.ForeignKey(Account, related_name='paths2ancestor')
	height = models.IntegerField(default=0)

	def __str__(self):
		return "{} -> {} | Height: {}".format(self.ancestor.name , self.descendant.name, self.height)

class Task(models.Model):
	desc = models.CharField(max_length=120)

	def __str__(self):
		return self.desc

	def get_absolute_url(self):
		return reverse('task_detail', kwargs={'pk': self.pk})

class Transaction(models.Model):
	desc = models.CharField(max_length=120)
	task = models.ForeignKey(Task)
	time = models.DateTimeField()

	def __str__(self):
		return self.desc

class Split(models.Model):
	account = models.ForeignKey(Account)
	change = models.IntegerField()
	transaction = models.ForeignKey(Transaction)

	def __str__(self):
		return "{} {:+}".format(self.account.name, self.change)
