# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic.edit import CreateView

class TaskListView(ListView):
	model = Task 

class TaskCreateView(CreateView):
	model = Task
	fields = ['desc']
	template_name_suffix = '_create_form'

class TaskDetailView(DetailView):
	model = Task
