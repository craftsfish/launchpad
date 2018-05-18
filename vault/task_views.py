# -*- coding: utf-8 -*-
from django.views.generic import DetailView
from task import *

class TaskDetailView(DetailView):
	model = Task

	def get_context_data(self, **kwargs):
		context = super(TaskDetailView, self).get_context_data(**kwargs)
		context['trans'] = self.object.transactions.all().order_by("time", "id")
		for t in context['trans']:
			t.ss = t.splits.all().order_by("id")
		return context
