# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView
from decimal import Decimal

class CommodityListView(ListView):
	model = Commodity

	def get_context_data(self, **kwargs):
		context = super(CommodityListView, self).get_context_data(**kwargs)
		for c in context['object_list']:
			cost = max((c.pvalue+c.pvat), (c.bvalue+c.bvat)) + c.express_in + c.express_out + c.wrap_fee
			c.price_tm = "{:.2f}".format(cost / Decimal(1 - 0.05))
			c.price_jd = "{:.2f}".format(cost / Decimal(1 - 0.08))
		return context
