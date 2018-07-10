# -*- coding: utf-8 -*-
from ground import *
from django.core.urlresolvers import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

class SecurityLoginRequiredMixin(LoginRequiredMixin):
	login_url = '/login/'

	def get_context_data(self, **kwargs):
		if 'nav_items' not in kwargs:
			i = NavItem()
			i.name = "退出"
			i.url = reverse('logout')
			kwargs['nav_items'] = [i]
		return super(SecurityLoginRequiredMixin, self).get_context_data(**kwargs)
