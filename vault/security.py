# -*- coding: utf-8 -*-
from ground import *
from django.core.urlresolvers import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from organization import *

class SecurityLoginRequiredMixin(LoginRequiredMixin):
	login_url = '/login/'

	def get_context_data(self, **kwargs):
		#common
		m = (
			("任务", reverse('task_list')),
			("物资", reverse('commodity_list')),
			("看板", reverse('compound_commodity_list')),
			("地域", reverse('address_list', kwargs={'key': 0})),
			("应收", reverse('receivable_commodity')),
			("修改密码", reverse('password_change')),
			("退出", reverse('logout')),
			(self.request.user.username, "#"),
		)
		l = []
		for name, url in m:
			i = NavItem()
			i.name = name
			i.url = url
			l.append(i)

		#books
		if self.request.user.has_perm('is_governor'):
			for i, o in enumerate(Organization.objects.filter(parent=None)):
				o.url = reverse('book_detail', kwargs={'pk': 1,'org': o.uuid})
				if len(o.name) > 2: #TODO, this algorithm is a quick solution
					o.name = o.name[2:4]
				l.insert(i, o)
			o = NavItem()
			o.url = reverse('customer_list', kwargs={'key': 0})
			o.name = '客户'
			l.insert(len(Organization.objects.filter(parent=None)), o)

		#home
		h = NavItem()
		h.name = "首页"
		h.url = reverse('chore_list')
		if self.request.user.has_perm('is_governor'):
			h.url = reverse('daily_task')
		l.insert(0, h)

		#assemble
		if 'nav_items' not in kwargs:
			kwargs['nav_items'] = l
		else:
			kwargs['nav_items'] += l

		#header
		if 'header' not in kwargs and hasattr(self, 'header'):
			kwargs['header'] = self.header
		return super(SecurityLoginRequiredMixin, self).get_context_data(**kwargs)
