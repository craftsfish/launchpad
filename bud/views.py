# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView

# Create your views here.
def index(request):
	root = Account.objects.get(name="/")
	children = []
	for p in root.paths2descendant.order_by("height").filter(height=1):
		children.append(p.descendant)
	return HttpResponse(children)

class AccountListView(ListView):
	model = Account

	def get_queryset(self):
		root = Account.objects.get(name="/")
		return root.descendants.all()

class AccountDetailView(DetailView):
	model = Account
