# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.views.generic import CreateView
from django.http import HttpResponseRedirect

class TransactionDetailView(DetailView):
	model = Transaction

	def get_context_data(self, **kwargs):
		context = super(TransactionDetailView, self).get_context_data(**kwargs)
		self.object.splits = self.object.split_set.all()
		return context

class TransactionUpdateView(UpdateView):
	model = Transaction
	fields = ['desc', 'time']
	template_name_suffix = '_update_form'

class TransactionCreateView(CreateView):
	model = Transaction
	fields = ['desc', 'time']
	template_name_suffix = '_create_form'

	def post(self, request, *args, **kwargs):
		desc = request.POST["desc"]
		time = request.POST["time"]
		t = Transaction(desc = request.POST["desc"], task = Task.objects.get(pk=kwargs['pk']), time = request.POST["time"])
		t.save()
		return HttpResponseRedirect(reverse('transaction_detail', args=[t.id]))
