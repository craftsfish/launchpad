# -*- coding: utf-8 -*-
from django.contrib.auth.mixins import LoginRequiredMixin

class SecurityLoginRequiredMixin(LoginRequiredMixin):
	login_url = '/login/'
