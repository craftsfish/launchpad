# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import DetailView

class SplitDetailView(DetailView):
	model = Split
