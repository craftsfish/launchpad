# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView

class OrganizationListView(ListView):
	model = Organization
