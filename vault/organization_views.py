# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView

class OrganizationListView(ListView):
	model = Organization

class OrganizationDetailView(DetailView):
	model = Organization

	def get_context_data(self, **kwargs):
		context = super(OrganizationDetailView, self).get_context_data(**kwargs)

		#2-dimension array to store account info for each [item, category] type
		matrix = []
		i=-1
		prev_item=None
		for a in self.object.accounts.all().order_by("item", "category"):
			if a.item != prev_item:
				prev_item = a.item
				i += 1
				matrix.append([a.item.name, 0, 0, 0, 0, 0])
			matrix[i][a.category+1] += a.balance
		context['matrix'] = matrix
		return context
