# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from django.db.models import Sum

class WalletListView(ListView):
	model = Wallet

	def get_context_data(self, **kwargs):
		context = super(WalletListView, self).get_context_data(**kwargs)
		for w in context['object_list']:
			w.category = "资产"
			if w.name.find("信用卡") == 0:
				w.category = "负债"
			w.balance = get_decimal_with_default(Account.objects.filter(name=w.name).aggregate(Sum('balance'))['balance__sum'], 0)
		return context

class WalletDetailView(ListView):
	model = Split
	paginate_by = 20

	def get_template_names(self):
		return ["%s/wallet_detail.html" % (Account._meta.app_label)]

	def get_queryset(self):
		self.object = Wallet.objects.get(pk=self.kwargs['pk'])
		return Split.objects.filter(account__name=self.object.name).order_by("-transaction__time", "-transaction__id", "-id")

	def get_context_data(self, **kwargs):
		context = super(WalletDetailView, self).get_context_data(**kwargs)

		#object
		context['object'] = self.object

		return context
