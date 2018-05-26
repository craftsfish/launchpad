# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView

class CommodityListView(ListView):
	model = Commodity
