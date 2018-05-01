# -*- coding: utf-8 -*-

from django.db import models
from supplier import *
import csv
from ground import *

class Item(models.Model):
	class Meta:
		unique_together = ("supplier", "name")
		ordering = ['supplier__id', 'name']

	name = models.CharField("品名", max_length=30, unique=True)
	supplier = models.ForeignKey(Supplier, verbose_name="供应商")
	value = models.DecimalField("价值", default=0, max_digits=8, decimal_places=2)

	def __str__(self):
		return self.name

	@staticmethod
	def Import():
		with open('/tmp/commodity.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			title = reader.next()
			columns = ["品名", "供应商"]
			for line in reader:
				n, sn = get_column_values(title, line, *columns)
				try:
					s = Supplier.objects.get(name=sn)
				except Supplier.DoesNotExist as e:
					s = Supplier(name=sn)
					s.save()
					print "增加供应商: {}".format(s)

				try:
					i = Item.objects.get(name=n)
				except Item.DoesNotExist as e:
					i = Item(name=n, supplier=s)
					i.save()
					print "增加物资: {}".format(i)
