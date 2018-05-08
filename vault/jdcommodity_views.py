# -*- coding: utf-8 -*-

from .models import *
from django.views.generic import ListView
from django.views.generic import CreateView

class JdcommodityListView(ListView):
	model = Jdcommodity

	def get_context_data(self, **kwargs):
		context = super(JdcommodityListView, self).get_context_data(**kwargs)
		for c in context['object_list']:
			c.map = Jdcommoditymap.objects.filter(jdcommodity=c).order_by("-since")[0]
			c.url = "https://item.jd.com/{}.html".format(c.id)
		return context

class JdcommoditymapCreateView(CreateView):
	model = Jdcommoditymap
	fields = ['since', 'items']
	template_name_suffix = '_create_form'
