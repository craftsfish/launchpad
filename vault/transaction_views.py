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
	pass
