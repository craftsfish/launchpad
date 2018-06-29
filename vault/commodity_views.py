# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from turbine import *

class CommodityListView(ListView):
	model = Commodity

class CommodityDetailView(DetailView):
	model = Commodity

	def get_context_data(self, **kwargs):
		span = 10
		threshold = 15
		context = super(CommodityDetailView, self).get_context_data(**kwargs)
		context['title'] = []
		for i, s in Itemstatus.choices:
			context['title'].append(s)

		context['repos'] = []
		if self.object.supplier:
			threshold = self.object.supplier.period
		threshold += 10
		for r in Account.objects.exclude(balance=0).filter(item=self.object).order_by('repository').values_list('repository', flat=True).distinct():
			r = Repository.objects.get(pk=r)

			#balance
			l = [r]
			context['repos'].append(l)
			total = 0
			for s in context['title']:
				v = Account.objects.filter(item=self.object).filter(repository=r).filter(name=s).aggregate(Sum('balance'))['balance__sum']
				if v: v = int(v)
				else: v = 0
				l.append(v)
				if s == "应发":
					total -= v
				else:
					total += v
			l.append(total)

			#shipment
			l += Turbine.get_shipping_out_information(self.object, r, span)

			#storage
			s = l[len(l)-1]
			l.append(threshold)
			l += Turbine.get_replenish_information(self.object, r, s, threshold)

		context['title'].append("合计")
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for i in range(span):
			context['title'].append((e-timedelta(i+1)).strftime("%m月%d日"))
		context['title'].append("出货速度")
		context['title'].append("目标库存天数")
		context['title'].append("实际库存天数")
		context['title'].append("补仓数量")
		return context
