# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from turbine import *
from .security import *

class CommodityListView(SecurityLoginRequiredMixin, ListView):
	model = Commodity

class CommodityStagnationListView(SecurityLoginRequiredMixin, TemplateView):
	template_name = "vault/commodity_stagnation_list.html"
	def get_context_data(self, **kwargs):
		result = []
		e = begin_of_day()
		candidates = Split.objects.filter(account__name="出货").filter(transaction__time__gte=(e-timedelta(90))).filter(transaction__time__lt=e).values_list('account__item', flat=True).distinct()
		for c in Commodity.objects.exclude(supplier=Supplier.objects.get(name='耗材')).order_by('-inproduction', 'supplier', 'name'):
			if c.id in candidates: continue
			c = Commodity.objects.get(pk=c)
			q = 0
			for i, s in Itemstatus.choices[1:3]:
				v = get_int_with_default(Account.objects.filter(item=c.item_ptr).filter(name=s).aggregate(Sum('balance'))['balance__sum'], 0)
				q += v
			if q != 0:
				c.quantity = q
				c.total = q * c.value
				result.append(c)
		kwargs['object_list'] = result
		return super(CommodityStagnationListView, self).get_context_data(**kwargs)

class RepositoryDetailInfo:
	pass

class CommodityDetailView(DetailView):
	model = Commodity

	def get_context_data(self, **kwargs):
		span = 10
		threshold = 15
		context = super(CommodityDetailView, self).get_context_data(**kwargs)
		context['title'] = []
		for i, s in Itemstatus.choices:
			context['title'].append(s)

		repositories = Account.objects.filter(item=self.object).order_by('repository').values_list('repository', flat=True).distinct()

		context['accounts'] = Account.objects.filter(item=self.object).order_by('organization', 'category', 'repository', 'name')
		context['repos'] = []
		if self.object.supplier:
			threshold = self.object.supplier.period
		threshold += 10
		for r in repositories:
			r = Repository.objects.get(pk=r)

			#balance
			l = [r]
			context['repos'].append(l)
			total = 0
			for s in context['title']:
				v = Account.objects.filter(item=self.object).filter(repository=r).filter(name=s).aggregate(Sum('balance'))['balance__sum']
				if v: v = int(v)
				else: v = 0
				i = RepositoryDetailInfo()
				i.v = v
				i.url = reverse('repository_detail', kwargs={'repo': r.id, 'commodity': self.object.id, 'status': Itemstatus.s2v(s)})
				l.append(i)
				if s == "应发":
					total -= v
				else:
					total += v
			l.append(total)
		context['title'].append("合计")

		context['statistic_title'] = []
		context['statistic'] = []
		for r in repositories:
			r = Repository.objects.get(pk=r)
			l = [r]
			context['statistic'].append(l)

			#shipment
			l += Turbine.get_shipping_out_information(self.object, r, span)

			#storage
			s = l[len(l)-1]
			l.append(threshold)
			l += Turbine.get_replenish_information(self.object, r, s, threshold)[1:]

		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for i in range(span):
			context['statistic_title'].append((e-timedelta(i+1)).strftime("%m月%d日"))
		context['statistic_title'].append("出货速度")
		context['statistic_title'].append("目标库存天数")
		context['statistic_title'].append("实际库存天数")
		context['statistic_title'].append("补仓数量")

		spans = [1,2,3,7,15,30,90,180,365]
		context['flow'] = []
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		item = self.object
		for span in spans:
			context['flow'].append([span] + item_flow_report(item, span, e))
		return context
