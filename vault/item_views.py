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
