# -*- coding: utf-8 -*-
from .models import *
from django.views.generic import ListView
from django.db.models import Sum

class RepositoryDetailView(ListView):
	model = Split
	paginate_by = 20

	def get_template_names(self):
		return ["%s/repository_detail.html" % (Account._meta.app_label)]

	def get_queryset(self):
		if not hasattr(self, "repository"):
			self.repository = Repository.objects.get(pk=self.kwargs['repo'])
			self.commodity = Commodity.objects.get(pk=self.kwargs['commodity'])
			self.status = Itemstatus.v2s(self.kwargs['status'])
		return Split.objects.filter(account__repository=self.repository).filter(account__item=self.commodity.item_ptr).filter(account__name=self.status).order_by("-transaction__time", "-transaction__id", "-id")

	def get_context_data(self, **kwargs):
		context = super(RepositoryDetailView, self).get_context_data(**kwargs)

		#object
		context['repository'] = self.repository
		context['commodity'] = self.commodity
		context['status'] = self.status
		context['balance'] = get_decimal_with_default(Account.objects.filter(repository=self.repository).filter(item=self.commodity.item_ptr).filter(name=self.status).aggregate(Sum('balance'))['balance__sum'], 0)

		#detail
		page = context['page_obj']
		total = get_decimal_with_default(self.get_queryset()[:self.paginate_by * (page.number - 1)].aggregate(Sum("change"))['change__sum'], 0)
		balance = context['balance'] - total
		for s in context["object_list"]:
			s.balance = balance
			balance -= s.change
			s.counters = s.transaction.splits.exclude(id=s.id)
		return context
