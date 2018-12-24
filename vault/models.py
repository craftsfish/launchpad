# -*- coding: utf-8 -*-
from django.db import models

class Platform(models.Model): #taobao, tmall, jd and etc.
	name = models.CharField(max_length=30, unique=True)

	def __str__(self):
		return self.name

from repository import *
from organization import *
from supplier import *
from item import *
from jdcommodity import *
from task import *
from jdorder import *
from account import *
from tmcommodity import *
from tmorder import *
from counterfeit import *
from wallet import *
from express import *

class Tmclear(models.Model):
	pid = models.CharField(max_length=30, primary_key=True, verbose_name="支付宝流水号")
	transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
	def __str__(self):
		return self.pid

class Jdorderclear(models.Model):
	pid = models.CharField(max_length=30, primary_key=True, verbose_name="单据编号")
	transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
	def __str__(self):
		return self.pid

class Jdwalletclear(models.Model):
	pid = models.CharField(max_length=40, primary_key=True, verbose_name="商户订单号")
	transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
	def __str__(self):
		return self.pid

class Jdadvertiseclear(models.Model):
	pid = models.IntegerField("序号", primary_key=True)
	transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
	def __str__(self):
		return self.pid

class CompoundCommodity(models.Model):
	name = models.CharField(max_length=30, verbose_name="组合名称")
	commodities = models.ManyToManyField(Commodity, verbose_name="商品")

	def __str__(self):
		s = ''
		for i in self.commodities.all():
			if s != '':
				s += ', '
			s += i.name
		return s

class Customer(models.Model):
	uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
	name = models.CharField(max_length=30)

	def __str__(self):
		return self.name

class Contact(models.Model):
	phone = models.IntegerField('电话', primary_key=True)
	customer = models.ForeignKey(Customer)

	def __str__(self):
		return self.customer.name + ': ' + self.phone

class Address(models.Model):
	name = models.CharField(max_length=120, unique=True)
	parent = models.ForeignKey('self', verbose_name="上级", null=True, blank=True, related_name="children")

	def __str__(self):
		return self.name
