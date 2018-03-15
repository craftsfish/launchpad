# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from .models import *

# Create your views here.
def index(request):
	root = Account.objects.get(name="/")
	children = []
	for p in root.paths2descendant.order_by("height").filter(height=1):
		children.append(p.descendant)
	return HttpResponse(children)
