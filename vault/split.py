# -*- coding: utf-8 -*-
from django.db import models
from account import *
from transaction import *

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
