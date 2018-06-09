# -*- coding: utf-8 -*-
from django.views.generic import TemplateView
from .models import *
from organization import *
from django import forms
from django.forms import formset_factory
from django.views.generic import FormView
from django.views.generic.base import ContextMixin
from django.http import HttpResponseRedirect

class JdorderForm(forms.Form):
	jdorder = forms.IntegerField()
	organization = forms.ModelChoiceField(queryset=Organization.objects)

class RetailForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	sale = forms.DecimalField(initial=0, max_digits=20, decimal_places=2)

class ChangeForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)

class CommodityShippingBaseForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	keyword = forms.CharField()

class CommodityShippingForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status = forms.ChoiceField(choices=Itemstatus.choices)
	keyword = forms.CharField()

class CommodityChangeRepositoryForm(forms.Form):
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_f = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.RadioSelect, initial=0)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_t = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.RadioSelect, initial=0)
	keyword = forms.CharField()

class CommodityDetailBaseForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	repository = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
CommodityDetailBaseFormSet = formset_factory(CommodityDetailBaseForm, extra=0)

class CommodityDetailForm(CommodityDetailBaseForm):
	status = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
CommodityDetailFormSet = formset_factory(CommodityDetailForm, extra=0)

class CommodityChangeRepositoryDetailForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_f = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_t = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
CommodityChangeRepositoryDetailFormSet = formset_factory(CommodityChangeRepositoryDetailForm, extra=0)

class FfsMixin(ContextMixin):
	"""
	A mixin that provides a way to show and handle form + formset in a request.
	"""
	form_class = None
	formset_class = None
	sub_form_class = None

	def get_context_data(self, **kwargs):
		if 'form' not in kwargs:
			kwargs['form'] = self.form_class()
		if 'sub_form' not in kwargs and self.sub_form_class:
			kwargs['sub_form'] = self.sub_form_class()
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
			print form.errors
			print formset.errors
			return self.render_to_response(self.get_context_data(form=form, formset=formset))

class JdorderMixin(FfsMixin):
	"""
	A mixin that provides a way to show and handle jdorder in a request.
	"""
	form_class = JdorderForm
	formset_class = CommodityDetailFormSet
	sub_form_class = CommodityShippingForm

	def formset_item_process(self, time, item, quantity, repository, status):
		pass

	def data_valid(self, form, formset):
		self.org = form.cleaned_data['organization']
		j = form.cleaned_data['jdorder']
		try:
			j = Jdorder.objects.get(oid=j)
		except Jdorder.DoesNotExist as e:
			j = Jdorder(oid=j, desc="京东订单")
			j.save()
		self.task = j.task_ptr
		t = timezone.now()
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			if not q: continue
			r = d['repository']
			s = Itemstatus.v2s(d['status'])
			self.formset_item_process(t, c.item_ptr, q, r, s)
		return super(JdorderMixin, self).data_valid(form, formset)

class DailyTaskView(TemplateView):
	template_name = "{}/daily_task.html".format(Organization._meta.app_label)

class RetailView(FfsMixin, TemplateView):
	template_name = "{}/retail.html".format(Organization._meta.app_label)
	form_class = RetailForm
	formset_class = CommodityDetailBaseFormSet
	sub_form_class = CommodityShippingBaseForm

	def data_valid(self, form, formset):
		self.task = Task(desc="销售")
		self.task.save()
		t = timezone.now()
		self.org = form.cleaned_data['organization']
		self.sale = form.cleaned_data['sale']
		v = 0
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			r = d['repository']
			Transaction.add(self.task, "出货", t, self.org, c.item_ptr, ("资产", "完好", r), -q, ("支出", "出货", r))
			v += q * c.value
		if self.sale == 0:
			self.sale = v
		cash = Money.objects.get(name="人民币")
		Transaction.add(self.task, "货款", t, self.org, cash.item_ptr, ("资产", "应收货款", None), self.sale, ("收入", "销售收入", None))
		return super(RetailView, self).data_valid(form, formset)

class ChangeView(FfsMixin, TemplateView):
	template_name = "{}/change.html".format(Organization._meta.app_label)
	form_class = ChangeForm
	formset_class = CommodityDetailFormSet
	sub_form_class = CommodityShippingForm

	def data_valid(self, form, formset):
		self.task = Task(desc="换货")
		self.task.save()
		t = timezone.now()
		o = form.cleaned_data['organization']
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			if not q: continue
			r = d['repository']
			s = Itemstatus.v2s(d['status'])
			if q > 0:
				Transaction.add(self.task, "换货.收货", t, o, c.item_ptr, ("资产", s, r), q, ("支出", "出货", r))
			else:
				Transaction.add(self.task, "换货.发货", t, o, c.item_ptr, ("资产", s, r), q, ("支出", "出货", r))
		return super(ChangeView, self).data_valid(form, formset)

class JdorderChangeView(JdorderMixin, TemplateView):
	template_name = "{}/jdorder_change.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status):
		if quantity > 0:
			Transaction.add(self.task, "换货.收货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		else:
			Transaction.add(self.task, "换货.发货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		return super(JdorderChangeView, self).formset_item_process(time, item, quantity, repository, status)

class JdorderCompensateView(JdorderMixin, TemplateView):
	template_name = "{}/jdorder_compensate.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status):
		Transaction.add(self.task, "补发", time, self.org, item, ("资产", status, repository), -quantity, ("支出", "出货", repository))
		return super(JdorderCompensateView, self).formset_item_process(time, item, quantity, repository, status)

class JdorderReturnView(JdorderMixin, TemplateView):
	template_name = "{}/jdorder_return.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status):
		Transaction.add(self.task, "退货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		return super(JdorderReturnView, self).formset_item_process(time, item, quantity, repository, status)

class ChangeRepositoryView(FfsMixin, TemplateView):
	template_name = "{}/change_repository.html".format(Organization._meta.app_label)
	form_class = ChangeForm
	formset_class = CommodityChangeRepositoryDetailFormSet
	sub_form_class = CommodityChangeRepositoryForm

	def data_valid(self, form, formset):
		self.task = Task(desc="换仓")
		self.task.save()
		t = timezone.now()
		o = form.cleaned_data['organization']
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			if not q: continue
			rf = d['repository_f']
			sf = Itemstatus.v2s(d['status_f'])
			rt = d['repository_t']
			st = Itemstatus.v2s(d['status_t'])
			Transaction.add(self.task, "换仓", t, o, c.item_ptr, ("资产", sf, rf), -q, ("资产", st, rt))
		return super(ChangeRepositoryView, self).data_valid(form, formset)
