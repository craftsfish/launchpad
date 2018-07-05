# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.http import HttpResponse
import json

class ItemListView(ListView):
	model = Item

	def post(self, request, *args, **kwargs):
		j = []
		for i in Item.objects.filter(name__contains=request.POST['keyword']):
			j.append({"id": i.id, "str": i.name})
		return HttpResponse(json.dumps(j))
