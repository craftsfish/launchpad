# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import ListView
from calibration_history import *

class CalibrationHistoryListView(ListView):
	model = CalibrationHistory
	paginate_by = 20

	def get_context_data(self, **kwargs):
		context = super(CalibrationHistoryListView, self).get_context_data(**kwargs)
		for o in context['object_list']:
			o.utc_human = datetime.fromtimestamp(o.utc)
		return context
