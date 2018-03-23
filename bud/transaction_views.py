# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import DetailView
from django.views.generic import UpdateView

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
