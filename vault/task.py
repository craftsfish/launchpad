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

	def delete_transactions_contains_desc(self, desc):
		for t in self.transactions.filter(desc__contains=desc):
			t.delete()

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

	def get_absolute_url(self):
		return reverse('task_detail', kwargs={'pk': self.pk})

	def uncleared_accounts(self):
		balance = {}
		for tr in self.transactions.all():
			for s in tr.splits.all():
				a = s.account
				if a.name.find("应") == 0:
					if balance.get(a.id) != None:
						balance[a.id] += s.change
					else:
						balance[a.id] = s.change
		for k, v in balance.items():
			if v == 0:
				balance.pop(k)
		return balance

	def candidates_of_repository_in(self):
		balance = {}
		for tr in self.transactions.all():
			for s in tr.splits.all():
				a = s.account
				if a.name.find("应收") == 0:
					if balance.get(a.id) != None:
						balance[a.id] += s.change
					else:
						balance[a.id] = s.change
		for k, v in balance.items():
			if v == 0:
				balance.pop(k)
		return balance

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

	def change_repository(self, origin, current):
		for s in self.splits.filter(account__repository=origin):
			a = s.account
			s.account = Account.get(a.organization, a.item, a.get_category_display(), a.name, current)
			s.save()

	@staticmethod
	def add(task, desc, time, organization, item, *args):
		tr = Transaction(desc=desc, task=task, time=time)
		tr.save()

		balance = 0
		i = 0
		while i < len(args):
			category, name, repository = args[i]
			a = Account.get(organization, item, category, name, repository)
			sign = a.sign()
			change = 0
			if i + 1 == len(args): #last item without change
				change = -balance / sign
			else:
				change = args[i+1]
			balance += sign * change
			i = i + 2;
			Split(account=a, change=change, transaction=tr).save()

		if balance != 0:
			print "[Error]交易帐目不平!" #TODO: raise exception

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
