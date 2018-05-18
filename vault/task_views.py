# -*- coding: utf-8 -*-
from django.views.generic import DetailView
from django.views.generic import ListView
from task import *

class TaskListView(ListView):
	model = Task
	paginate_by = 20

class TaskDetailView(DetailView):
	model = Task

	def get_context_data(self, **kwargs):
		context = super(TaskDetailView, self).get_context_data(**kwargs)
		context['trans'] = self.object.transactions.all().order_by("time", "id")
		for t in context['trans']:
			t.ss = t.splits.all().order_by("id")
		return context
