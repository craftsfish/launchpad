# -*- coding: utf-8 -*-

from .models import *
from django import forms
from django.views.generic import FormView
from django.utils import timezone

class ShippingForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects.all(), label="进/出货单位")

class ShippingInCreateView(FormView):
	template_name = "{}/shipping_form.html".format(Organization._meta.app_label)
	form_class = ShippingForm

	def post(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['task_id'])
		p = self.request.POST
		o = Organization.objects.get(pk=p['organization'])
		for i in range(int(p['items_total'])):
			if p.get("invoice_{}_include".format(i)) == "on":
				it = Item.objects.get(pk=p["invoice_{}_item".format(i)])
				q = int(p["invoice_{}_quantity".format(i)])
				self.task.add_transaction("进货", timezone.now(), o, it, ("资产", "应收"), q, ("收入", "进货"))
				self.task.add_transaction("货款", timezone.now(), o, Item.objects.get(name="人民币"), ("负债", "应付货款"), q*it.value, ("支出", "进货"))
		return super(ShippingInCreateView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(ShippingInCreateView, self).get_context_data(**kwargs)
		context['items'] = Item.objects.all()
		for i, j in enumerate(context['items']):
			j.name_check = "invoice_{}_include".format(i)
			j.name_item = "invoice_{}_item".format(i)
			j.name_quantity = "invoice_{}_quantity".format(i)
		return context
