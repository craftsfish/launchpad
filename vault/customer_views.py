# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from .security import *

class CustomerListView(SecurityLoginRequiredMixin, ListView):
	model = Customer
	paginate_by = 1

	def get_queryset(self):
		#if self.kwargs['key'] == 0:
		return Customer.objects.order_by("counterfeit", 'recruit', 'join')
		#return Customer.objects.filter(contact__phone='19971579166').order_by("counterfeit", 'recruit', 'join')

	def get_context_data(self, **kwargs):
		context = super(CustomerListView, self).get_context_data(**kwargs)
		for t in context['object_list']:
			t.flag = "买家"
			if t.counterfeit:
				t.flag = "刷手"
			t.join = utc_2_datetime(t.join).astimezone(timezone.get_current_timezone())
			t.recruited = True
			if t.recruit == 0:
				t.recruited = False
			t.recruit = utc_2_datetime(t.recruit).astimezone(timezone.get_current_timezone())
			t.jdorders = Jdorder.objects.filter(contact__in=t.contact_set.all()).all()
			t.tmorders = Tmorder.objects.filter(contact__in=t.contact_set.all()).all()
			def __key(o):
				return o.time
			t.orders = sorted(list(t.jdorders) + list(t.tmorders), key=__key)
		return context
