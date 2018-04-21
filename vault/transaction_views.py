# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django import forms
from django.contrib.admin import widgets
from django.views.generic import DetailView
from django.views.generic import UpdateView

class TransactionForm(forms.ModelForm):
	class Meta:
		model = Transaction
		fields = ['desc', 'time', 'task']
		widgets = {'task': forms.HiddenInput()}
	time = forms.SplitDateTimeField(widget=widgets.AdminSplitDateTime())

class TransactionMixin(object):
	model = Transaction
	form_class = TransactionForm

class TransactionDetailView(TransactionMixin, DetailView):
	def get_context_data(self, **kwargs):
		context = super(TransactionDetailView, self).get_context_data(**kwargs)
		context['splits'] = self.object.splits.all()
		return context

class TransactionUpdateView(TransactionMixin, UpdateView):
	def get_context_data(self, **kwargs):
		context = super(TransactionUpdateView, self).get_context_data(**kwargs)
		splits = self.object.splits.all()
		for i, s in enumerate(splits):
			s.id_id = "id_splits_{}_id".format(i)
			s.id_account = "id_splits_{}_account".format(i)
			s.id_change = "id_splits_{}_change".format(i)
			s.id_delete = "id_splits_{}_delete".format(i)
		context['splits'] = splits
		return context

	def form_valid(self, form):
		return super(TransactionUpdateView, self).form_valid(form)
