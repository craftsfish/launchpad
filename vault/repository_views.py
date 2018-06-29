# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from django.db.models import Sum

class RepositoryDetailView(ListView):
	model = Split

	def get_template_names(self):
		return ["%s/repository_detail.html" % (Account._meta.app_label)]
