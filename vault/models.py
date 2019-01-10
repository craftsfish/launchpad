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
	uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
	name = models.CharField(max_length=30)
	join = models.IntegerField("初次下单时间", default=0)
	counterfeit = models.BooleanField('刷手标记', default=True)
	recruit = models.IntegerField("招募时间", default=0)

	def __str__(self):
		if self.counterfeit:
			return self.name + "(刷手)"
		else:
			return self.name + "(买家)"

class Contact(models.Model):
	phone = models.CharField('电话', max_length=30, primary_key=True)
	customer = models.ForeignKey(Customer)

	def __str__(self):
		return self.customer.name + ': ' + self.phone

class Address(models.Model):
	name = models.CharField(max_length=120)
	parent = models.ForeignKey('self', verbose_name="上级", null=True, blank=True, related_name="children")
	level = models.IntegerField('层级', default=0)

	class Meta:
		unique_together = ("name", "parent")

	def __str__(self):
		return self.name

	@staticmethod
	def get_parent(address):
		address = address.replace(' ', '')
		province = None
		city = None
		provinces = Address.objects.filter(level=2)
		for i in provinces:
			idx = address.find(i.name)
			if idx == 0:
				province = i
				address = address[len(i.name.encode('utf-8')):]
				break
		if province == None:
			print address
			return None, None
		if address.find('省') == 0:
				address = address[len('省'.encode('utf-8')):]
		if address.find('自治区') != -1:
				address = address[address.find('自治区') + len('自治区'.encode('utf-8')):]
		if len(Address.objects.filter(parent=province, level=1)):
			for i in Address.objects.filter(parent=province):
				idx = address.find(i.name)
				if idx == 0:
					city = i
					address = address[idx+len(i.name.encode('utf-8')):]
					break
			if city == None:
				print address
				return None, None
		if address.find('市') == 0:
				address = address[len('市'.encode('utf-8')):]
		parent = city
		if parent == None:
			parent = province
		return parent, address

	@staticmethod
	def add(address):
		parent, address = Address.get_parent(address)
		if parent == None:
			return None
		a, created = Address.objects.get_or_create(name=address, parent=parent)
		#print "{} {} {}".format(parent.parent, parent, address)
		a.save()
		return a
