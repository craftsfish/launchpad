# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.views.generic import CreateView
from django.http import HttpResponseRedirect
from django.contrib.admin import widgets
from django import forms

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
		self.object.splits = self.object.split_set.all()
		return context

class TransactionUpdateView(TransactionMixin, UpdateView):
	pass

class TransactionCreateView(TransactionMixin, CreateView):
	def get_initial(self):
		initial = super(TransactionCreateView, self).get_initial()
		initial['task'] = Task.objects.get(pk=self.kwargs['pk']).id
		return initial
