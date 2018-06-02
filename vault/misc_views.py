# -*- coding: utf-8 -*-
from django.views.generic import TemplateView
from organization import *

class DailyTaskView(TemplateView):
	template_name = "{}/daily_task.html".format(Organization._meta.app_label)
