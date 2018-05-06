# -*- coding: utf-8 -*-

from .models import *
from django.views.generic import ListView

class JdcommodityListView(ListView):
	model = Jdcommodity

	def get_context_data(self, **kwargs):
		context = super(JdcommodityListView, self).get_context_data(**kwargs)
		return context
