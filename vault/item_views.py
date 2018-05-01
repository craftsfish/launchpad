# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView

class ItemListView(ListView):
	model = Item
	paginate_by = 100
