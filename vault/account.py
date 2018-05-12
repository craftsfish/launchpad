# -*- coding: utf-8 -*-
from django.db import models
from organization import *
from item import *
from .models import *

# Create your models here.
class Account(models.Model):
	class Meta:
		unique_together = ("organization", "item", "category", "name")

	name = models.CharField("名称", max_length=30, null=True, blank=True)
	balance = models.DecimalField("余额", default=0, max_digits=20, decimal_places=2)
	organization = models.ForeignKey(Organization, verbose_name="组织", related_name="accounts")
	item = models.ForeignKey(Item, verbose_name="物资")
	ACCOUNT_CATEGORY_CHOICES = (
		(0, "资产"),
		(1, "负债"),
		(2, "收入"),
		(3, "支出"),
		(4, "所有者权益"),
	)
	category = models.IntegerField(choices=ACCOUNT_CATEGORY_CHOICES, default=0)

	def __str__(self):
		return "{}.{}.{}.{}".format(str(self.organization), self.item.name, self.get_category_display(), self.name)

	@staticmethod
	def get(o, i, c, n):
		hit = False
		for j,v in Account.ACCOUNT_CATEGORY_CHOICES:
			if v == c:
				hit = True
				break
		if not hit:
			print "非法账户类型: {}".format(c)
			return None

		try:
			return Account.objects.filter(organization=o).filter(item=i).filter(category=j).get(name=n)
		except Account.DoesNotExist as e:
			a = Account(organization=o, item=i, category=j, name=n)
			a.save()
			print "[账户]增加新账户: {}".format(a)
			return a
