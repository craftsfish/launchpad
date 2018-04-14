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

		self.object.descendants()
		def __get_cell(matrix, item, category):
			r = matrix.get(item)
			if r == None:
				item_name = Item.objects.get(pk=item).name
				matrix[item] = [item_name, [0, [], []], [0, [], []], [0, [], []], [0, [], []], [0, [], []]]
			return matrix[item][category+1]

		#2-dimension (item, category) array to store account info which include each sub-organization and direct account
		matrix = {}

		#direct monitored account
		for a in self.object.accounts.all().order_by("item", "category"):
			c = __get_cell(matrix, a.item.id, a.category)
			c[0] += a.balance #accumulation of total
			c[2].append(a)

		#TODO: sub organizations

		context['matrix'] = matrix
		return context
