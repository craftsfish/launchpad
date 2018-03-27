# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import DetailView
from django.views.generic import CreateView
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
