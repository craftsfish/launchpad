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

	def get_context_data(self, **kwargs):
		context = super(TaskDetailView, self).get_context_data(**kwargs)
		print self.object
		for t in self.object.transaction_set.all():
			print t.desc
		context['transactions'] = self.object.transaction_set.all()
		return context
