# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView

class ItemListView(ListView):
	model = Item
	paginate_by = 100

class ItemDetailView(DetailView):
	model = Item

	def get_context_data(self, **kwargs):
		context = super(ItemDetailView, self).get_context_data(**kwargs)
		return context
