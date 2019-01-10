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

class CompoundCommodityListView(SecurityLoginRequiredMixin, ListView):
	model = CompoundCommodity

def shipping_info_of_commodities(commodities, end, span):
	result = []
	for i in range(span):
		q = Split.objects.filter(account__item__in=commodities).filter(account__organization=Organization.objects.get(name='泰福高腾复专卖店')).filter(account__name="出货")
		q = q.filter(transaction__time__gte=(end-timedelta(1))).filter(transaction__time__lt=end)
		v = q.aggregate(Sum('change'))['change__sum']
		v = get_int_with_default(v, 0)
		q = q.filter(transaction__desc__contains='刷单.回收')
		w = q.aggregate(Sum('change'))['change__sum']
		w = -get_int_with_default(w, 0)
		end -= timedelta(1)
		result.append([end, v, w])
	return result

def place_info_of_commodities(commodities, end, span):
	info = []
	result = {}
	q = Split.objects.filter(account__item__in=commodities).filter(account__organization=Organization.objects.get(name='泰福高腾复专卖店')).filter(account__name="出货")
	q = q.filter(transaction__time__gte=(end-timedelta(span))).filter(transaction__time__lt=end)
	for s in q:
		if s.transaction.task.tmorder.counterfeit != None:
			continue
		a = s.transaction.task.tmorder.address
		if a == None:
			continue
		key = a.parent.id
		if result.get(key) == None:
			result[key] = 0
		result[key] += s.change

	def __key(i):
		k, v = i
		a = Address.objects.get(id=k)
		if a.level == 1:
			return a.parent.id * 100000 + a.id
		else:
			return a.id * 100000
	for k, v in sorted(result.items(), key=__key):
		a = Address.objects.get(id=k)
		s = a.name
		if a.level == 1:
			s = a.parent.name + a.name
		info.append([s, v])
	return info

class CompoundCommodityDetailView(DetailView):
	model = CompoundCommodity

	def get_context_data(self, **kwargs):
		context = super(CompoundCommodityDetailView, self).get_context_data(**kwargs)
		obj = context['object']
		place = place_info_of_commodities(obj.commodities.all(), begin_of_day(), 30)
		info = shipping_info_of_commodities(obj.commodities.all(), begin_of_day(), 30)
		for i, j, k in info:
			print "{}: 出货: {}, 刷单: {}".format(i, j, k)
		context['info'] = info
		context['place'] = place
		return context
