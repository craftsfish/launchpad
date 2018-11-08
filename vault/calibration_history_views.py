# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import ListView
from calibration_history import *

class CalibrationHistoryListView(ListView):
	model = CalibrationHistory
	paginate_by = 20
