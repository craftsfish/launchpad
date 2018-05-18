# -*- coding: utf-8 -*-

from .models import *
from django import forms
from django.views.generic import FormView

class ShippingForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects.all())

class ShippingInCreateView(FormView):
	template_name = "{}/shipping_form.html".format(Organization._meta.app_label)
	form_class = ShippingForm

	def post(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['task_id'])
		return super(ShippingInCreateView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(ShippingInCreateView, self).get_context_data(**kwargs)
		context['items'] = Item.objects.all()
		return context
