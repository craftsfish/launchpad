# -*- coding: utf-8 -*-

from .models import *
from django import forms
from django.views.generic import FormView

class ShippingForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects.all())

class ShippingInCreateView(FormView):
	template_name = "{}/shipping_form.html".format(Organization._meta.app_label)
	form_class = ShippingForm
