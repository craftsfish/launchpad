# -*- coding: utf-8 -*-
from django.views.generic import DetailView
from task import *

class TaskDetailView(DetailView):
	model = Task

	def get_context_data(self, **kwargs):
		context = super(TaskDetailView, self).get_context_data(**kwargs)
		return context
