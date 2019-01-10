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
				return Address.objects.filter(level=2).filter(name='北京')
