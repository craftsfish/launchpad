# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django.views.generic import ListView
from django.views import View
from django.db.models import Sum
from django.http import HttpResponse
from django.core import serializers

class AccountListView(View):
	def get(self, request, *args, **kwargs):
		r = Account.objects.all()[:2]
		return HttpResponse(serializers.serialize("json", r))

# Split list that build upon this account is displayed
class AccountDetailView(ListView):
	model = Split
	paginate_by = 2

	def __get_object(self):
		self.object = Account.objects.get(pk=self.kwargs['pk'])

	def get_template_names(self):
		return ["%s/account_detail.html" % (Account._meta.app_label)]

	def get_queryset(self):
		self.__get_object()
		return Split.objects.filter(account=self.object).order_by("-transaction__time", "-transaction__id", "-id")

	def get_context_data(self, **kwargs):
		context = super(AccountDetailView, self).get_context_data(**kwargs)

		#object
		context['object'] = self.object

		#balance
		balance = self.object.balance
		page = context['page_obj']
		total = self.get_queryset()[:self.paginate_by * (page.number - 1)].aggregate(Sum("change"))['change__sum']
		if not total:
			total = 0
		balance -= total
		for s in context["object_list"]:
			s.balance = balance
			balance -= s.change

		return context
