# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import DetailView

class BookDetailView(DetailView):
	model = Item
	template_name = "{}/book_detail.html".format(Item._meta.app_label)

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
