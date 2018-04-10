# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils import timezone
from django.core.urlresolvers import reverse

# Create your models here.
class Supplier(models.Model):
	name = models.CharField(max_length=30, unique=True)
	abbrev = models.CharField(max_length=10, unique=True)

	def __str__(self):
		return self.name

class Commodity(models.Model):
	class Meta:
		unique_together = ("supplier", "name")
		ordering = ['supplier__id', 'name']

	name = models.CharField("品名", max_length=30)
	supplier = models.ForeignKey(Supplier, verbose_name="供应商")
	package = models.IntegerField("箱规", default=0) #how many items is included in a package when purchasing
	express_in = models.DecimalField("运费.进货", default=0, max_digits=8, decimal_places=2)
	express_out = models.DecimalField("运费.出货",default=0, max_digits=8, decimal_places=2)
	wrap_fee = models.DecimalField("包装费", default=0, max_digits=8, decimal_places=2)
	note = models.CharField("备注", max_length=300, blank=True)

	#for buy
	bvalue = models.DecimalField("进价.购买", default=0, max_digits=8, decimal_places=2)
	bvat = models.DecimalField("进项税.购买", default=0, max_digits=8, decimal_places=2)

	#for purchase
	pvalue = models.DecimalField("进价.批发", default=0, max_digits=8, decimal_places=2)
	pvat = models.DecimalField("进项税.批发", default=0, max_digits=8, decimal_places=2)

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('commodity_list')

class Organization(models.Model):
	class Meta:
		ordering = ['id']

	name = models.CharField(max_length=30)
	ancestors = models.ManyToManyField('self', through='Opath', through_fields=('descendant', 'ancestor'), symmetrical=False, related_name="descendants")

	def save(self, *args, **kwargs):
		super(Organization, self).save(*args, **kwargs)

		#add path (self -> self)
		path2self = Opath.objects.filter(ancestor=self.id).filter(descendant=self.id)
		if len(path2self) == 0:
			Opath(ancestor=self, descendant=self).save()

	def parent(self):
		p = Opath.objects.all().filter(descendant=self.id).filter(height=1)
		if len(p) != 1:
			return None
		return p[0].ancestor

	def set_parent(self, parent):
		d = self.descendants.all().values_list('id', flat=True)
		if self.parent(): #remove obsolete paths
			a = self.ancestors.all().exclude(id=self.id).values_list('id', flat=True)
			Opath.objects.all().filter(ancestor__in=a).filter(descendant__in=d).delete()

		cur = self
		while parent:
			for _d in d:
				h = Opath.objects.filter(ancestor=cur.id).filter(descendant=_d).values_list("height", flat=True)[0]
				Opath(ancestor=parent, descendant=Organization.objects.get(id=_d), height=h+1).save()
			cur = parent
			parent = cur.parent()

	def get_absolute_url(self):
		return reverse('organization_detail', kwargs={'pk': self.pk})

	def __str__(self):
		return self.name

class Opath(models.Model):
	class Meta:
		unique_together = ("ancestor", "descendant")

	ancestor = models.ForeignKey(Organization, related_name='paths2descendant')
	descendant = models.ForeignKey(Organization, related_name='paths2ancestor')
	height = models.IntegerField(default=0)

	def __str__(self):
		return "{} -> {} | Height: {}".format(self.ancestor.name , self.descendant.name, self.height)

class Account(models.Model):
	class Meta:
		ordering = ['id']

	name = models.CharField("名称", max_length=30)
	balance = models.DecimalField("余额", default=0, max_digits=20, decimal_places=2)
	ancestors = models.ManyToManyField('self', through='Apath', through_fields=('descendant', 'ancestor'), symmetrical=False, related_name="descendants")
	organization = models.ForeignKey(Organization, verbose_name="隶属于")
	commodity = models.ForeignKey(Commodity, verbose_name="物品")
	ACCOUNT_CATEGORY_CHOICES = (
		(0, "资产"),
		(1, "负债"),
		(2, "收入"),
		(3, "支出"),
		(4, "净资产"),
	)
	category = models.IntegerField(choices=ACCOUNT_CATEGORY_CHOICES, default=0)

	def save(self, *args, **kwargs):
		super(Account, self).save(*args, **kwargs)

		#add path (self -> self)
		path2self = Apath.objects.filter(ancestor=self.id).filter(descendant=self.id)
		if len(path2self) == 0:
			Apath(ancestor=self, descendant=self).save()

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('account_detail', kwargs={'pk': self.pk})

	def parent(self):
		p = Apath.objects.all().filter(descendant=self.id).filter(height=1)
		if len(p) != 1:
			return None
		return p[0].ancestor

	def set_parent(self, parent):
		d = self.descendants.all().values_list('id', flat=True)
		if self.parent(): #remove obsolete paths
			a = self.ancestors.all().exclude(id=self.id).values_list('id', flat=True)
			Apath.objects.all().filter(ancestor__in=a).filter(descendant__in=d).delete()

		cur = self
		while parent:
			for _d in d:
				h = Apath.objects.all().filter(ancestor=cur.id).filter(descendant=_d).values_list("height", flat=True)[0]
				Apath(ancestor=parent, descendant=Account.objects.get(id=_d), height=h+1).save()
			cur = parent
			parent = cur.parent()

	def children(self):
		ids = Apath.objects.all().filter(ancestor=self.id).filter(height=1).values_list("descendant", flat=True)
		return Account.objects.filter(id__in=ids)

	def is_leaf(self):
		return len(self.children()) == 0

	def delete_paths2ancestor(self):
		self.paths2ancestor.all().delete()

class Apath(models.Model):
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

	def delete(self, *args, **kwargs):
		for t in self.transaction_set.all():
			t.delete()
		super(Task, self).delete(*args, **kwargs)

class Transaction(models.Model):
	desc = models.CharField(max_length=120)
	task = models.ForeignKey(Task)
	time = models.DateTimeField()

	def __str__(self):
		return self.desc

	def get_absolute_url(self):
		return reverse('transaction_detail', kwargs={'pk': self.pk})

	def delete(self, *args, **kwargs):
		for s in self.split_set.all():
			s.delete()
		super(Transaction, self).delete(*args, **kwargs)

class Split(models.Model):
	account = models.ForeignKey(Account)
	change = models.DecimalField(max_digits=20, decimal_places=2)
	transaction = models.ForeignKey(Transaction)

	def __str__(self):
		return "{} {:+}".format(self.account.name, self.change)

	def get_absolute_url(self):
		return reverse('split_detail', kwargs={'pk': self.pk})

	def save(self, *args, **kwargs):
		if self.id:
			orig = Split.objects.get(pk=self.id)
			orig.account.balance -= orig.change
			orig.account.save()
		#reload account to reflect changes made in previous instructions
		account = Account.objects.get(pk=self.account.id)
		account.balance += self.change
		account.save()
		super(Split, self).save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		self.account.balance -= self.change
		self.account.save()
		super(Split, self).delete(*args, **kwargs)

