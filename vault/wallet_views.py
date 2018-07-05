# -*- coding: utf-8 -*-
from .models import *
from .security import *
from django.views.generic import ListView
from django.db.models import Sum

class WalletDetailView(ListView):
	model = Split
	paginate_by = 64

	def get_template_names(self):
		return ["%s/wallet_detail.html" % (Account._meta.app_label)]

	def get_queryset(self):
		if not hasattr(self, "object"):
			self.object = Wallet.objects.get(pk=self.kwargs['pk'])
		return Split.objects.filter(account__name=self.object.name).order_by("-transaction__time", "-transaction__id", "-id")

	def get_context_data(self, **kwargs):
		context = super(WalletDetailView, self).get_context_data(**kwargs)

		#object
		context['object'] = self.object
		self.object.balance = get_decimal_with_default(Account.objects.filter(name=self.object.name).aggregate(Sum('balance'))['balance__sum'], 0)

		#detail
		page = context['page_obj']
		total = get_decimal_with_default(self.get_queryset()[:self.paginate_by * (page.number - 1)].aggregate(Sum("change"))['change__sum'], 0)
		balance = self.object.balance - total
		for s in context["object_list"]:
			s.balance = balance
			balance -= s.change
			s.counters = s.transaction.splits.exclude(id=s.id)
		return context
