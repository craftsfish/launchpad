# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import DetailView
from django.views.generic import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic import UpdateView
from django.core.urlresolvers import reverse
from django import forms

class SplitForm(forms.ModelForm):
	class Meta:
		model = Split
		fields = ['account', 'change', 'transaction']
		widgets = {'transaction': forms.HiddenInput()}

class SplitDetailView(DetailView):
	model = Split

class SplitCreateView(CreateView):
	model = Split
	form_class = SplitForm

	def get_initial(self):
		initial = super(SplitCreateView, self).get_initial()
		initial['transaction'] = Transaction.objects.get(pk=self.kwargs['pk']).id
		return initial

class SplitDeleteView(DeleteView):
	model = Split

	def get_success_url(self):
		return reverse('transaction_detail', kwargs={'pk': self.object.transaction.id})

class SplitUpdateView(UpdateView):
	model = Split
	form_class = SplitForm
