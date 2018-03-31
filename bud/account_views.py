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
from django.views.generic.edit import DeleteView
from django.core.urlresolvers import reverse_lazy
from django.db.models import Sum

# Create your views here.
class AccountListView(ListView):
	model = Account

	def get_queryset(self):
		return Account.root().children()

# Split list that build upon this account is displayed
class AccountDetailView(ListView):
	model = Split
	paginate_by = 2

	def get_template_names(self):
		return ["%s/account_detail.html" % (Account._meta.app_label)]

	def get_queryset(self):
		a = Account.objects.get(pk=self.kwargs['pk'])
		return Split.objects.filter(account=a).order_by("-transaction__time", "-transaction__id", "-id")

	def get_context_data(self, **kwargs):
		context = super(AccountDetailView, self).get_context_data(**kwargs)

		#object
		self.object = Account.objects.get(pk=self.kwargs['pk'])
		context['object'] = self.object

		#descendants
		descendants = []
		for p in self.object.paths2descendant.filter(height__gte=1).order_by("height"):
			descendants.append(p.descendant)
		context['descendants'] = descendants

		#ancestors
		ancestors = []
		for p in self.object.paths2ancestor.order_by("-height"):
			ancestors.append(p.ancestor)
		context['ancestors'] = ancestors

		#edit
		if self.object != Account.root(): #root account is forbidden for edit
			context['editable'] = True
		if self.object.is_leaf():
			context['deletable'] = True

		#balance
		balance = self.object.balance
		page = context['page_obj']
		total = self.get_queryset()[:self.paginate_by * (page.number - 1)].aggregate(Sum("change"))['change__sum']
		if not total:
			total = 0
		balance -= total
		for s in context["object_list"]:
			s.balance = balance
			balance -= s.change

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

class AccountCreateView(CreateView):
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

class AccountDeleteView(DeleteView):
	model = Account
	success_url = reverse_lazy('account_index')

	def post(self, request, *args, **kwargs):
		self.get_object().delete_paths2ancestor()
		return super(AccountDeleteView, self).post(request, *args, **kwargs)
