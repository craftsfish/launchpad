# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView

class ItemListView(ListView):
	model = Item
	paginate_by = 100

	def get_context_data(self, **kwargs):
		context = super(ItemListView, self).get_context_data(**kwargs)
		for item in context["object_list"]:
			candidates = set() #root organizations that operates item
			for o in Account.objects.filter(item=item).values_list('organization', flat=True).distinct():
				candidates.add(Organization.objects.get(pk=o).root())
			item.orgs = candidates
		return context

class ItemDetailView(DetailView):
	model = Item

	def get(self, request, *args, **kwargs):
		self.org = Organization.objects.get(pk=kwargs['org'])
		return super(ItemDetailView, self).get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(ItemDetailView, self).get_context_data(**kwargs)
		context['org'] = self.org
		total = [0, 0, 0, 0, 0]
		#orgs = [{}, {}, {}, {}, {}]
		accounts = [[], [], [], [], []]

		#direct monitored accounts
		for a in Account.objects.filter(item=self.object).filter(organization=self.org).order_by("category", "name"):
			c = a.category
			total[c] += a.balance
			accounts[c].append(a)
		context['accounts'] = accounts
		context['total'] = total

		return context
