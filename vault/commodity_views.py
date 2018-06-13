# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

class CommodityListView(ListView):
	model = Commodity

class CommodityDetailView(DetailView):
	model = Commodity

	@staticmethod
	def __get_shipping_out_information(commodity, repository, span):
		r = []
		speed = 0
		active = 0
		decay = 0.7
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for i in range(span):
			q = Split.objects.filter(account__item=commodity).filter(account__repository=repository).filter(account__name="出货")
			q = q.filter(transaction__time__gte=(e-timedelta(1))).filter(transaction__time__lt=e)
			v = q.aggregate(Sum('change'))['change__sum']
			if v: v = int(v)
			else: v = 0
			r.append(v)
			speed += decay ** i * (1 - decay) * v
			if v: active += 1
			e -= timedelta(1)
		speed = speed * active / span
		r.append(speed)
		return r

	@staticmethod
	def __get_replenish_information(commodity, repository, speed, threshold):
		inventory = Account.objects.filter(item=commodity).filter(repository=repository).filter(name__in=["完好", "应收"]).aggregate(Sum('balance'))['balance__sum']
		if inventory: inventory = int(inventory)
		else: inventory = 0
		if speed <= 0:
			return [8888, -inventory]
		else:
			return [inventory/speed, speed * threshold - inventory]

	def get_context_data(self, **kwargs):
		span = 10
		threshold = 15 #TODO, modify with each supplier's particular limitaion
		context = super(CommodityDetailView, self).get_context_data(**kwargs)
		context['title'] = []
		for i, s in Itemstatus.choices:
			context['title'].append(s)
		context['title'].append("应收")

		context['repos'] = []
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
				total += v
			l.append(total)

			#shipment
			l += CommodityDetailView.__get_shipping_out_information(self.object, r, span)

			#storage
			s = l[len(l)-1]
			l.append(threshold)
			l += CommodityDetailView.__get_replenish_information(self.object, r, s, threshold)

		context['title'].append("合计")
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for i in range(span):
			context['title'].append((e-timedelta(i+1)).strftime("%m月%d日"))
		context['title'].append("出货速度")
		context['title'].append("目标库存天数")
		context['title'].append("实际库存天数")
		context['title'].append("补仓数量")

		return context
