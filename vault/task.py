# -*- coding: utf-8 -*-
from django.db import models
from account import *

class Task(models.Model):
	desc = models.CharField(max_length=120)

	def __str__(self):
		return self.desc

	def delete(self, *args, **kwargs):
		for t in self.transactions.all():
			t.delete()
		super(Task, self).delete(*args, **kwargs)

	def add_transaction(self, desc, time, organization, item, *args):
		tr = Transaction(desc=desc, task=self, time=time)
		tr.save()

		balance = 0
		i = 0
		while i < len(args):
			category, name = args[i]
			a = Account.get(organization, item, category, name)
			sign = a.sign()
			change = 0
			if i + 1 == len(args): #last item
				change = -balance / sign
				i = i + 1
			else:
				change = args[i+1]
				balance += sign * change
				i = i + 2;
			Split(account=a, change=change, transaction=tr).save()

class Transaction(models.Model):
	class Meta:
		ordering = ['-time', '-id']

	desc = models.CharField(max_length=120)
	task = models.ForeignKey(Task, null=True, blank=True, related_name="transactions")
	time = models.DateTimeField()

	def __str__(self):
		return self.desc

	def get_absolute_url(self):
		return reverse('transaction_detail', kwargs={'pk': self.pk})

	def delete(self, *args, **kwargs):
		for s in self.splits.all():
			s.delete()
		super(Transaction, self).delete(*args, **kwargs)

class Split(models.Model):
	account = models.ForeignKey(Account)
	change = models.DecimalField(max_digits=20, decimal_places=2)
	transaction = models.ForeignKey(Transaction, related_name="splits")

	def __str__(self):
		return "{} {:+}".format(self.account.name, self.change)

	#def get_absolute_url(self):
		#return reverse('split_detail', kwargs={'pk': self.pk})

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
