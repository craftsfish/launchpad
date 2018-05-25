# -*- coding: utf-8 -*-

from django.db import models
from supplier import *
import csv
from ground import *

class Item(models.Model):
	class Meta:
		ordering = ['name']

	name = models.CharField("品名", max_length=30, unique=True)

	def __str__(self):
		return self.name

class Commodity(Item):
	supplier = models.ForeignKey(Supplier, verbose_name="供应商", null=True, blank=True)
	value = models.DecimalField("价值", default=0, max_digits=8, decimal_places=2)
	onsale = models.BooleanField("在售", default=True) #在售/下架
	inproduction = models.BooleanField("在产", default=True) #在产/停产

	@staticmethod
	def Import():
		with open('/tmp/commodity.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			title = reader.next()
			columns = ["品名", "供应商"]
			for line in reader:
				n, sn = get_column_values(title, line, *columns)
				if sn != None:
					try:
						s = Supplier.objects.get(name=sn)
					except Supplier.DoesNotExist as e:
						s = Supplier(name=sn)
						s.save()
						print "增加供应商: {}".format(s)

				try:
					i = Commodity.objects.get(name=n)
				except Commodity.DoesNotExist as e:
					i = Commodity(name=n, supplier=s)
					try:
						i.item_ptr = Item.objects.get(name=n)
					except Item.DoesNotExist as e:
						i.item_ptr = None
					i.save()
					print "增加物资: {}".format(i)

class Money(Item):
	@staticmethod
	def Import():
		with open('/tmp/money.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			for l in reader:
				n = l[0]
				try:
					i = Money.objects.get(name=n)
				except Money.DoesNotExist as e:
					i = Money(name=n)
					try:
						i.item_ptr = Item.objects.get(name=n)
					except Item.DoesNotExist as e:
						i.item_ptr = None
					i.save()
					print "增加货币: {}".format(i)
