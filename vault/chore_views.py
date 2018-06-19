# -*- coding: utf-8 -*-
from django.views.generic import TemplateView
from organization import *

class ChoreListView(TemplateView):
	template_name = "{}/chore.html".format(Organization._meta.app_label)
