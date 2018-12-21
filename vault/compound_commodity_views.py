# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from turbine import *
from .security import *

class CompoundCommodityListView(SecurityLoginRequiredMixin, ListView):
	model = CompoundCommodity

class CompoundCommodityDetailView(DetailView):
	model = CompoundCommodity

	def get_context_data(self, **kwargs):
		context = super(CompoundCommodityDetailView, self).get_context_data(**kwargs)
		return context
