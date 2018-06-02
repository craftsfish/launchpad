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
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	repository = forms.ModelChoiceField(queryset=Repository.objects)
	sale = forms.DecimalField(initial=0, max_digits=20, decimal_places=2)

class RetailCommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	name = forms.CharField(max_length=30, disabled=True, required=False)
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
		context['formset'] = RetailCommodityFormSet()
		return context
