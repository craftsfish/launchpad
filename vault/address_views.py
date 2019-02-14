# -*- coding: utf-8 -*-
from .models import *
from django.db.models import Q
from django.views.generic import ListView
from .security import *

class AddressListView(SecurityLoginRequiredMixin, ListView):
	model = Address

	def get_queryset(self):
		k = self.kwargs['key']
		if k == '0':
			return Address.objects.filter(level=2).filter(name='北京')
		else:
			parent, address = Address.get_parent(k.encode('utf-8'))
			if parent:
				return Address.objects.filter(id=parent.id)
			else:
				city = Address.get_city(k.encode('utf-8'))
				if city:
					return Address.objects.filter(name=city.name)
				return Address.objects.filter(level=2).filter(name='北京')

	def get_context_data(self, **kwargs):
		context = super(AddressListView, self).get_context_data(**kwargs)
		for i in context['object_list']:
			q = Tmorder.objects.filter(address__parent=i.id)
			end = begin_of_day()
			span = 30
			q = q.filter(time__gte=(end-timedelta(span))).filter(time__lt=end).order_by('address__name', '-time')
			i.orders = []
			for o in q:
				if o.counterfeit == None:
					continue
				i.orders.append(o)
				s_addr = ''
				if o.address:
					s_addr = o.address.name
				o.addr = s_addr
				o.customer = o.contact.customer
		return context
