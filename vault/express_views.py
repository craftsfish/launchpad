# -*- coding: utf-8 -*-
from .models import *
from .security import *
from django.views.generic import ListView

class ExpressListView(ListView):
	model = Express

	def get_template_names(self):
		return "vault/express_list.html"

	def get_queryset(self):
		return Express.objects.filter(eid=int(self.kwargs['id']))
