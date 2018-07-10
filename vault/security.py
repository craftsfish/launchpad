# -*- coding: utf-8 -*-
from ground import *
from django.core.urlresolvers import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

class SecurityLoginRequiredMixin(LoginRequiredMixin):
	login_url = '/login/'

	def get_context_data(self, **kwargs):
		m = (
			("修改密码", reverse('password_change')),
			("退出", reverse('logout')),
		)
		l = []
		for name, url in m:
			i = NavItem()
			i.name = name
			i.url = url
			l.append(i)
		if 'nav_items' not in kwargs:
			kwargs['nav_items'] = l
		else:
			kwargs['nav_items'] += l

		#header
		if 'header' not in kwargs and hasattr(self, 'header'):
			kwargs['header'] = self.header
		return super(SecurityLoginRequiredMixin, self).get_context_data(**kwargs)
