# -*- coding: utf-8 -*-
from .models import *
from .security import *
from django.views.generic import ListView

class ExpressListView(ListView):
	model = Express
	paginate_by = 64

	def get_template_names(self):
		return "vault/express_list.html"
