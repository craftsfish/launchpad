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
	name = models.CharField("名称", max_length=30, unique=True)
	balance = models.BigIntegerField(default=0)
	#ancestors = models.ManyToManyField('self', through='Path', through_fields=('descendant', 'ancestor'), symmetrical=False, related_name="descendants")

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('account_detail', kwargs={'pk': self.pk})

class Path(models.Model): 
	ancestor = models.ForeignKey(Account, related_name='paths2descendant')
	descendant = models.ForeignKey(Account, related_name='paths2ancestor')
	height = models.IntegerField(default=0)

	def __str__(self):
		return "{} -> {} | Height: {}".format(self.ancestor.name , self.descendant.name, self.height)

class Task(models.Model):
	desc = models.CharField(max_length=120)

	def __str__(self):
		return self.desc

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
