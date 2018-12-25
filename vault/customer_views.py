# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from .security import *

class CustomerListView(SecurityLoginRequiredMixin, ListView):
	model = Customer
	paginate_by = 50

	def get_queryset(self):
		#if self.kwargs['key'] == 0:
		return Customer.objects.order_by("counterfeit", 'recruit', 'join')

	def get_context_data(self, **kwargs):
		context = super(CustomerListView, self).get_context_data(**kwargs)
		for t in context['object_list']:
			t.flag = "买家"
			if t.counterfeit:
				t.flag = "刷手"
			t.join = utc_2_datetime(t.join).astimezone(timezone.get_current_timezone())
			t.recruit = utc_2_datetime(t.recruit).astimezone(timezone.get_current_timezone())
		return context


