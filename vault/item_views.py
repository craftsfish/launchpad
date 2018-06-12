# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.http import HttpResponse
import json

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

	def post(self, request, *args, **kwargs):
		j = []
		for i in Item.objects.filter(name__contains=request.POST['keyword']):
			j.append({"id": i.id, "str": i.name})
		return HttpResponse(json.dumps(j))

class BookDetailView(DetailView):
	model = Item

	def get(self, request, *args, **kwargs):
		self.org = Organization.objects.get(pk=kwargs['org'])
		return super(BookDetailView, self).get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(BookDetailView, self).get_context_data(**kwargs)
		context['org'] = self.org
		total = [0, 0, 0, 0, 0]
		orgs = [{}, {}, {}, {}, {}]
		accounts = [[], [], [], [], []]

		#direct monitored accounts
		has_account = False
		for a in Account.objects.filter(item=self.object).filter(organization=self.org).order_by("category", "name"):
			c = a.category
			total[c] += a.balance
			accounts[c].append(a)
			has_account = True
		if has_account:
			context['accounts'] = accounts

		#sub organizations
		has_orgs = False
		for o in self.org.children.all():
			sub_orgs = [o] + o.descendants()
			for a in Account.objects.filter(item=self.object).filter(organization__in=sub_orgs):
				c = a.category
				total[c] += a.balance
				if orgs[c].get(o.id) == None:
					orgs[c][o.id] = [o, 0]
				orgs[c][o.id][1] += a.balance
				has_orgs = True
		if has_orgs:
			context['orgs'] = orgs

		#total
		context['total'] = total
		return context
