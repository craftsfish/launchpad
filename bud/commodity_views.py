# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from decimal import Decimal
from django import forms
from django.views.generic import ListView
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.views.generic import FormView
from django.core.urlresolvers import reverse_lazy

class CommodityListView(ListView):
	model = Commodity

	def get_context_data(self, **kwargs):
		context = super(CommodityListView, self).get_context_data(**kwargs)
		for c in context['object_list']:
			cost = max((c.pvalue+c.pvat), (c.bvalue+c.bvat)) + c.express_in + c.express_out + c.wrap_fee
			c.price_tm = "{:.2f}".format(cost / Decimal(1 - 0.05))
			c.price_jd = "{:.2f}".format(cost / Decimal(1 - 0.08))
		return context

class CommodityCreateView(CreateView):
	model = Commodity
	fields = ['name', 'supplier', 'package', 'express_in', 'express_out', 'wrap_fee', 'note', 'bvalue', 'bvat', 'pvalue', 'pvat']
	template_name_suffix = '_create_form'

class CommodityDetailView(DetailView):
	model = Commodity

class CommodityUpdateView(UpdateView):
	model = Commodity
	fields = ['name', 'supplier', 'package', 'express_in', 'express_out', 'wrap_fee', 'note', 'bvalue', 'bvat', 'pvalue', 'pvat']
	template_name_suffix = '_update_form'

class UploadFileForm(forms.Form):
    file = forms.FileField()

class CommodityImportView(FormView):
	template_name = "commodity_upload_file.html"
	form_class = UploadFileForm
	success_url = reverse_lazy('commodity_list')

	def form_valid(self, form):
		return super(CommodityImportView, self).form_valid(form)
