# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.db.models import Sum

class CommodityListView(ListView):
	model = Commodity

class CommodityDetailView(DetailView):
	model = Commodity

	def get_context_data(self, **kwargs):
		context = super(CommodityDetailView, self).get_context_data(**kwargs)
		context['title'] = []
		for i, s in Itemstatus.choices:
			context['title'].append(s)
		context['title'].append("应收")
		context['repos'] = []
		for r in Account.objects.exclude(balance=0).filter(item=self.object).order_by('repository').values_list('repository', flat=True).distinct():
			r = Repository.objects.get(pk=r)
			j = [r]
			context['repos'].append(j)
			total = 0
			for s in context['title']:
				v = Account.objects.filter(item=self.object).filter(repository=r).filter(name=s).aggregate(Sum('balance'))['balance__sum']
				if v: v = int(v)
				else: v = 0
				j.append(v)
				total += v
			j.append(total)
		context['title'].append("合计")
		return context
