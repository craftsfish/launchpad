# -*- coding: utf-8 -*-
from django.views.generic import TemplateView
from .models import *
from organization import *
from django import forms
from django.forms import formset_factory
from django.views.generic import FormView

class DailyTaskView(TemplateView):
	template_name = "{}/daily_task.html".format(Organization._meta.app_label)

class RetailForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects, empty_label=None)
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	sale = forms.DecimalField(initial=0, max_digits=20, decimal_places=2)

class RetailCommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
RetailCommodityFormSet = formset_factory(RetailCommodityForm, extra=0)

class RetailView(FormView):
	template_name = "{}/retail.html".format(Organization._meta.app_label)
	form_class = RetailForm

	def post(self, request, *args, **kwargs):
		self.task = Task(desc="销售")
		self.task.save()
		t = timezone.now()
		form = RetailForm(self.request.POST)
		if form.is_valid():
			o = form.cleaned_data['organization']
			r = form.cleaned_data['repository']
			s = form.cleaned_data['sale']
		v = 0
		formset = RetailCommodityFormSet(self.request.POST)
		if formset.is_valid():
			for f in formset:
				d = f.cleaned_data
				if d['check']:
					c = Commodity.objects.get(pk=d['id'])
					q = d['quantity']
					Transaction.add(self.task, "出货", t, o, c.item_ptr, ("资产", "完好", r), -q, ("支出", "出货", r))
					v += q * c.value
		if s == 0:
			print "hit"
			s = v
		cash = Money.objects.get(name="人民币")
		Transaction.add(self.task, "货款", t, o, cash.item_ptr, ("资产", "应收货款", None), s, ("收入", "销售收入", None))
		return super(RetailView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(RetailView, self).get_context_data(**kwargs)
		context['formset'] = RetailCommodityFormSet(auto_id=False)
		return context

class ChangeForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects, empty_label=None)
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status = forms.ChoiceField(choices=Itemstatus.choices)
	ship = forms.ChoiceField(choices=Shipstatus.choices)

class ChangeCommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	repository = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
	ship = forms.ChoiceField(choices=Shipstatus.choices, widget=forms.HiddenInput)
ChangeCommodityFormSet = formset_factory(ChangeCommodityForm, extra=0)

class ChangeView(FormView):
	template_name = "{}/change.html".format(Organization._meta.app_label)
	form_class = ChangeForm

	def post(self, request, *args, **kwargs):
		self.task = Task(desc="换货")
		self.task.save()
		t = timezone.now()
		form = ChangeForm(self.request.POST)
		if form.is_valid():
			o = form.cleaned_data['organization']
		formset = ChangeCommodityFormSet(self.request.POST)
		if formset.is_valid():
			for f in formset:
				d = f.cleaned_data
				if d['check']:
					c = Commodity.objects.get(pk=d['id'])
					q = d['quantity']
					if not q:
						continue
					r = d['repository']
					s = Itemstatus.v2s(d['status'])
					if q > 0:
						Transaction.add(self.task, "换货.收货", t, o, c.item_ptr, ("资产", s, r), q, ("支出", "出货", r))
					else:
						Transaction.add(self.task, "换货.发货", t, o, c.item_ptr, ("资产", s, r), q, ("支出", "出货", r))
		return super(ChangeView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(ChangeView, self).get_context_data(**kwargs)
		context['formset'] = ChangeCommodityFormSet(auto_id=False)
		return context

class ChangeRepositoryForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects, empty_label=None)
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_f = forms.ChoiceField(choices=Itemstatus.choices)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_t = forms.ChoiceField(choices=Itemstatus.choices)

class ChangeRepositoryCommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_f = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_t = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
ChangeRepositoryCommodityFormSet = formset_factory(ChangeRepositoryCommodityForm, extra=0)

class ChangeRepositoryView(FormView):
	template_name = "{}/change_repository.html".format(Organization._meta.app_label)
	form_class = ChangeRepositoryForm

	def get_context_data(self, **kwargs):
		context = super(ChangeRepositoryView, self).get_context_data(**kwargs)
		formset_initial = [
						{
							'id': 3,
							'quantity': 5,
							'check': True,
							'repository_f': Repository.objects.get(name="孤山仓"),
							'status_f': 0,
							'repository_t': Repository.objects.get(name="南京仓"),
							'status_t': 2,
						}]
		context['formset'] = ChangeRepositoryCommodityFormSet(initial = formset_initial, auto_id=False)
		for f in context['formset']:
			f.label = Repository.objects.get(pk=f['repository_f'].value()).name + "."
			f.label += Itemstatus.v2s(f['status_f'].value()) + " -> "
			f.label += Repository.objects.get(pk=f['repository_t'].value()).name + "."
			f.label += Itemstatus.v2s(f['status_t'].value()) + ": "
			f.label += Commodity.objects.get(pk=f['id'].value()).name
		return context
