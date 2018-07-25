# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import TemplateView
from django.views.generic import ListView
from django.views.generic import DetailView
from django.http import HttpResponse
import json
from django.contrib.auth.mixins import PermissionRequiredMixin
from .security import *
from .turbine import *

class ItemListView(ListView):
	model = Item

	def post(self, request, *args, **kwargs):
		j = []
		for i in Item.objects.filter(name__contains=request.POST['keyword']):
			j.append({"id": i.id, "str": i.name})
		return HttpResponse(json.dumps(j))

class ItemFlowView(SecurityLoginRequiredMixin, PermissionRequiredMixin, TemplateView):
	template_name = "vault/item_flow.html"
	permission_required = ('is_governor')

	def get_context_data(self, **kwargs):
		kwargs['candidates'] = []
		spans = [1,2,3,7,15,30,90,180,365]
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for item in Commodity.objects.order_by('supplier', 'name'):
			item.data = []
			for span in spans:
				item.data += item_flow_report(item, span, e)
			kwargs['candidates'].append(item)
			kwargs['spans'] = spans
		return super(ItemFlowView, self).get_context_data(**kwargs)
