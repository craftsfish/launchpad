# -*- coding: utf-8 -*-
from django.views.generic import TemplateView
from .models import *
from organization import *
from django import forms
from django.forms import formset_factory
from django.views.generic import FormView
from django.views.generic.base import ContextMixin
from django.http import HttpResponseRedirect

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

class JdorderChangeForm(ChangeForm):
	jdorder = forms.IntegerField()

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

class JdorderChangeView(FormView):
	template_name = "{}/jdorder_change.html".format(Organization._meta.app_label)
	form_class = JdorderChangeForm

	def post(self, request, *args, **kwargs):
		t = timezone.now()
		form = JdorderChangeForm(self.request.POST)
		if form.is_valid():
			o = form.cleaned_data['organization']
			j = form.cleaned_data['jdorder']
			try:
				j = Jdorder.objects.get(oid=j)
			except Jdorder.DoesNotExist as e:
				j = Jdorder(oid=j, desc="京东订单")
				j.save()
			self.task = j.task_ptr
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
		return super(JdorderChangeView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(JdorderChangeView, self).get_context_data(**kwargs)
		context['formset'] = ChangeCommodityFormSet(auto_id=False)
		return context

class JdorderCompensateForm(forms.Form):
	jdorder = forms.IntegerField()
	organization = forms.ModelChoiceField(queryset=Organization.objects, empty_label=None)
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status = forms.ChoiceField(choices=Itemstatus.choices)

class CompensateCommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	repository = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
CompensateCommodityFormSet = formset_factory(CompensateCommodityForm, extra=0)

class JdorderCompensateView(FormView):
	template_name = "{}/jdorder_compensate.html".format(Organization._meta.app_label)
	form_class = JdorderCompensateForm

	def post(self, request, *args, **kwargs):
		t = timezone.now()
		form = JdorderCompensateForm(self.request.POST)
		if form.is_valid():
			o = form.cleaned_data['organization']
			j = form.cleaned_data['jdorder']
			try:
				j = Jdorder.objects.get(oid=j)
			except Jdorder.DoesNotExist as e:
				j = Jdorder(oid=j, desc="京东订单")
				j.save()
			self.task = j.task_ptr
		else:
			print form.errors
			print self.request.POST
		formset = CompensateCommodityFormSet(self.request.POST)
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
					Transaction.add(self.task, "补发", t, o, c.item_ptr, ("资产", s, r), -q, ("支出", "出货", r))
		return super(JdorderCompensateView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(JdorderCompensateView, self).get_context_data(**kwargs)
		context['formset'] = CompensateCommodityFormSet(auto_id=False)
		return context

class FfsMixin(ContextMixin):
	"""
	A mixin that provides a way to show and handle form + formset in a request.
	"""
	form_class = None
	formset_class = None

	def get_context_data(self, **kwargs):
		if 'form' not in kwargs:
			kwargs['form'] = self.form_class()
		if 'formset' not in kwargs:
			kwargs['formset'] = self.formset_class(auto_id=False)
		return super(FfsMixin, self).get_context_data(**kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def data_valid(self, form, formset):
		return HttpResponseRedirect(self.get_success_url())

	def post(self, request, *args, **kwargs):
		form = self.form_class(self.request.POST)
		formset = self.formset_class(self.request.POST)
		if form.is_valid() and formset.is_valid():
			return self.data_valid(form, formset)
		else:
			return self.render_to_response(self.get_context_data(form=form, formset=formset))


class JdorderReturnForm(forms.Form):
	jdorder = forms.IntegerField()
	organization = forms.ModelChoiceField(queryset=Organization.objects, empty_label=None)
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status = forms.ChoiceField(choices=Itemstatus.choices)

class JdorderReturnView(FfsMixin, TemplateView):
	template_name = "{}/jdorder_return.html".format(Organization._meta.app_label)
	form_class = JdorderReturnForm
	formset_class = CompensateCommodityFormSet

	def data_valid(self, form, formset):
		t = timezone.now()
		o = form.cleaned_data['organization']
		j = form.cleaned_data['jdorder']
		try:
			j = Jdorder.objects.get(oid=j)
		except Jdorder.DoesNotExist as e:
			j = Jdorder(oid=j, desc="京东订单")
			j.save()
		self.task = j.task_ptr

		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			if not q:
				continue
			r = d['repository']
			s = Itemstatus.v2s(d['status'])
			Transaction.add(self.task, "退货", t, o, c.item_ptr, ("资产", s, r), q, ("支出", "出货", r))
		return super(JdorderReturnView, self).data_valid(form, formset)

class ChangeRepositoryForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects, empty_label=None)
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.RadioSelect, empty_label=None, initial=1)
	status_f = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.RadioSelect, initial=0)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.RadioSelect, empty_label=None, initial=1)
	status_t = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.RadioSelect, initial=0)

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

	def post(self, request, *args, **kwargs):
		self.task = Task(desc="换仓")
		self.task.save()
		t = timezone.now()
		form = ChangeRepositoryForm(self.request.POST)
		if form.is_valid():
			o = form.cleaned_data['organization']
		formset = ChangeRepositoryCommodityFormSet(self.request.POST)
		if formset.is_valid():
			for f in formset:
				d = f.cleaned_data
				if d['check']:
					c = Commodity.objects.get(pk=d['id'])
					q = d['quantity']
					if not q:
						continue
					rf = d['repository_f']
					sf = Itemstatus.v2s(d['status_f'])
					rt = d['repository_t']
					st = Itemstatus.v2s(d['status_t'])
					Transaction.add(self.task, "换仓", t, o, c.item_ptr, ("资产", sf, rf), -q, ("资产", st, rt))
		return super(ChangeRepositoryView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(ChangeRepositoryView, self).get_context_data(**kwargs)
		context['formset'] = ChangeRepositoryCommodityFormSet(auto_id=False)
		return context
