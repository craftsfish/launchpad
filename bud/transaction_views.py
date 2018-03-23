# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.forms import ModelForm
from django.forms import modelformset_factory

class TransactionDetailView(DetailView):
	model = Transaction

	def get_context_data(self, **kwargs):
		context = super(TransactionDetailView, self).get_context_data(**kwargs)
		self.object.splits = self.object.split_set.all()
		return context

SplitFormSet = modelformset_factory(Split, fields = ("account", "change"))

class TransactionUpdateView(UpdateView):
	model = Transaction
	fields = ['desc']
	template_name_suffix = '_update_form'

	def get_context_data(self, **kwargs):
		context = super(TransactionUpdateView, self).get_context_data(**kwargs)
		self.object.splits = SplitFormSet(queryset=self.object.split_set.all())
		return context
