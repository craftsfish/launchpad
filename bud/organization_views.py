# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView

class OrganizationListView(ListView):
	model = Organization

class OrganizationDetailView(DetailView):
	model = Organization
