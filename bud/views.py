# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import UpdateView

# Create your views here.
def index(request):
	root = Account.objects.get(name="/")
	children = []
	for p in root.paths2descendant.order_by("height").filter(height=1):
		children.append(p.descendant)
	return HttpResponse(children)

class AccountListView(ListView):
	model = Account

class AccountDetailView(DetailView):
	model = Account

	def get_context_data(self, **kwargs):
		context = super(AccountDetailView, self).get_context_data(**kwargs)

		#children
		children = []
		for p in self.object.paths2descendant.order_by("height").filter(height=1):
			children.append(p.descendant)
		context['children'] = children

		#ancestors
		ancestors = []
		for p in self.object.paths2ancestor.order_by("-height"):
			ancestors.append(p.ancestor)
		context['ancestors'] = ancestors

		return context

class AccountUpdateView(UpdateView):
	model = Account
	fields = ['name']
	template_name_suffix = '_update_form'
