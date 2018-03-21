# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.views.generic.edit import CreateView
from django.forms import ModelForm
from django.forms import Form
from django import forms

# Create your views here.
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

class ParentAccountForm(forms.Form):
	parent = forms.ModelChoiceField(Account.objects, label="父账户")

class AccountUpdateView(UpdateView):
	model = Account
	fields = ['name']
	template_name_suffix = '_update_form'

	def get_context_data(self, **kwargs):
		context = super(AccountUpdateView, self).get_context_data(**kwargs)
		parent = self.object.parent()
		if parent:
			context['parent'] = ParentAccountForm({"parent": parent.id})
		else:
			context['parent'] = ParentAccountForm()
		return context

	def post(self, request, *args, **kwargs):
		parent_id = request.POST["parent"]
		parent = None
		if parent_id != "":
			parent = Account.objects.all().get(id=parent_id)
		account = self.get_object()
		if parent in account.descendants.all():
			return HttpResponse("XXX 是当前账户的子账户，不能设定为当前账户的父亲!!!")
		else:
			account.set_parent(parent)
			return super(AccountUpdateView, self).post(request, *args, **kwargs)

class ChildAccountCreateView(CreateView):
	model = Account
	fields = ['name']
	template_name_suffix = '_create_form'

	def post(self, request, *args, **kwargs):
		parent = self.get_object()
		n = request.POST["name"]
		if n not in Account.objects.filter(id__in=parent.children()).values_list("name", flat=True):
			a = Account(name=n)
			a.save()
			Path(ancestor=a, descendant=a, height=0).save()
			a.set_parent(parent)
			return HttpResponseRedirect(reverse('account_detail', args=[a.id]))
		else:
			return HttpResponse("子账户已经存在!!!")
