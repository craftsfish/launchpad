# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView

class CommodityListView(ListView):
	model = Commodity

class CommodityDetailView(DetailView):
	model = Commodity
