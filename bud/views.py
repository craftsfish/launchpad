# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.forms import ModelForm

# Create your views here.
class AccountListView(ListView):
	model = Account

	def get_queryset(self):
		root = Account.objects.get(name="/")
		return Account.objects.raw("select a.descendant_id as id from bud_path as a where a.ancestor_id = {} order by a.height, a.descendant_id".format(root.id))

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

class PathForm(ModelForm):
	class Meta:
		model = Path
		fields = ["ancestor"]
		labels = {
			"ancestor": "父账户",
		}

class AccountUpdateView(UpdateView):
	model = Account
	fields = ['name']
	template_name_suffix = '_update_form'

	def get_context_data(self, **kwargs):
		context = super(AccountUpdateView, self).get_context_data(**kwargs)
		parent = Path.objects.all().filter(descendant=self.object).filter(height=1)[0]
		context['parent'] = PathForm(instance=parent)
		return context

	def post(self, request, *args, **kwargs):
		parent = Account.objects.all().get(id=request.POST["ancestor"])
		account = self.get_object()
		if len(Path.objects.all().filter(ancestor=account).filter(descendant=parent).filter(height__gt=0)) != 0:
			return HttpResponse("XXX 是当前账户的子账户，不能设定为当前账户的父亲!!!")
		else:
			#TODO: update path here
			return super(AccountUpdateView, self).post(request, *args, **kwargs)
