# -*- coding: utf-8 -*-
from .models import *
from .security import *
from django.views.generic import DetailView

class BookDetailView(SecurityLoginRequiredMixin, DetailView):
	model = Item
	template_name = "{}/book_detail.html".format(Item._meta.app_label)

	def get(self, request, *args, **kwargs):
		self.org = Organization.objects.get(uuid=kwargs['org'])
		return super(BookDetailView, self).get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(BookDetailView, self).get_context_data(**kwargs)
		total = [0, 0, 0, 0, 0]
		orgs = self.org.dfs_tree()
		for o in orgs:
			o.accounts_info = ([], [], [], [], []) #for each category
			for a in Account.objects.filter(item=self.object).filter(organization=o).order_by("category", "name"):
				c = a.category
				total[c] += a.balance
				o.accounts_info[c].append(a)
		context['organization'] = self.org
		context['organizations'] = orgs
		context['total'] = total
		return context
