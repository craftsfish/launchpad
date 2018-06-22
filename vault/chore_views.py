# -*- coding: utf-8 -*-
from django.views.generic import TemplateView
from organization import *
from wallet import *

class ChoreListView(TemplateView):
	template_name = "{}/chore.html".format(Organization._meta.app_label)

	def get_context_data(self, **kwargs):
		context = super(ChoreListView, self).get_context_data(**kwargs)
		context['wallet_wechat'] = Wallet.objects.get(name="运营资金.微信")
		context['wallet_alipay'] = Wallet.objects.get(name="运营资金.支付宝")
		return context
