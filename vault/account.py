# -*- coding: utf-8 -*-
from django.db import models
from organization import *
from repository import *
from item import *
from .models import *

# Create your models here.
class Account(models.Model):
	class Meta:
		unique_together = ("organization", "item", "category", "repository", "name")

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
	category = models.IntegerField(choices=ACCOUNT_CATEGORY_CHOICES, verbose_name="会计类目", default=0)
	repository = models.ForeignKey(Repository, verbose_name="仓库", null=True, blank=True)

	def __str__(self):
		r = self.organization.name + '.' + self.get_category_display()
		if self.repository:
			r += '.' + self.repository.name
		return r + '.' + self.name

	def sign(self):
		signs = [1, -1, -1, 1, -1]
		return signs[self.category]

	@staticmethod
	def str2category(s):
		for i, v in Account.ACCOUNT_CATEGORY_CHOICES:
			if v == s:
				return i
		return -1

	@staticmethod
	def get(o, i, c, n, r=None):
		c = Account.str2category(c)
		try:
			return Account.objects.filter(organization=o).filter(item=i).filter(category=c).filter(repository=r).get(name=n)
		except Account.DoesNotExist as e:
			a = Account(organization=o, item=i, category=c, repository=r, name=n)
			a.save()
			print "[账户]增加新账户: {}.{}.{}".format(a.organization, a.item, a)
			return a
