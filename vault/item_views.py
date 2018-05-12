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
		candidates = set() #root organizations that operates item
		for o in Account.objects.filter(item=self.object).values_list('organization', flat=True).distinct():
			candidates.add(Organization.objects.get(pk=o).root())
		for c in candidates:
			print c
		return context
