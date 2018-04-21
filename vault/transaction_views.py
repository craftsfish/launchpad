# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django import forms
from django.contrib.admin import widgets
from django.forms import inlineformset_factory
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

SplitFormSet = inlineformset_factory(Transaction, Split, fields=('change', 'account'), widgets = {'account': forms.HiddenInput()}, labels = {'change': ''}, extra=0)
class TransactionUpdateView(TransactionMixin, UpdateView):
	def get_context_data(self, **kwargs):
		context = super(TransactionUpdateView, self).get_context_data(**kwargs)
		context['formset'] = SplitFormSet(instance=self.object)
		for f in context['formset']:
			f.account_display_name = str(f.instance.account)
		return context

	def form_valid(self, form):
		formset = SplitFormSet(self.request.POST, self.request.FILES, instance=self.object)
		if formset.is_valid():
			formset.save()
		return super(TransactionUpdateView, self).form_valid(form)
