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
		fields = ['desc', 'time']
	time = forms.DateTimeField(widget=widgets.AdminSplitDateTime())

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
	def post(self, request, *args, **kwargs):
		desc = request.POST["desc"]
		time = request.POST["time"]
		t = Transaction(desc = request.POST["desc"], task = Task.objects.get(pk=kwargs['pk']), time = request.POST["time"])
		t.save()
		return HttpResponseRedirect(reverse('transaction_detail', args=[t.id]))
