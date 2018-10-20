# -*- coding: utf-8 -*-
import uuid
from django.db import models
from organization import *
from repository import *
from item import *
from .models import *

# Create your models here.
class Account(models.Model):
	class Meta:
		unique_together = ("organization", "item", "category", "repository", "name")

	uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
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

	def derive_with_new_organization(self, organization):
		return Account.objects.get_or_create(organization=organization, item=self.item, category=self.category, repository=self.repository, name=self.name)[0]

	@staticmethod
	def str2category(s):
		for i, v in Account.ACCOUNT_CATEGORY_CHOICES:
			if v == s:
				return i
		return -1

	@staticmethod
	def get_or_create(o, i, c, n, r=None):
		c = Account.str2category(c)
		obj, created = Account.objects.get_or_create(organization=o, item=i, category=c, repository=r, name=n)
		if created: print "[账户]增加<{}>账户: {}".format(obj.item, obj)
		return obj

	@staticmethod
	def get(o, i, c, n, r=None):
		c = Account.str2category(c)
		return Account.objects.get(organization=o, item=i, category=c, repository=r, name=n)
