# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import RedirectView
from django.views.generic import DetailView
from .models import *
from account import *
from django.views.generic import ListView
from django.views import View
from django.db.models import Sum
from django.http import HttpResponse
import json
from django.utils import timezone
from .security import *

class AccountListView(View):
	def post(self, request, *args, **kwargs):
		r = Account.objects.all().order_by("category", "name")

		#filter
		p = request.POST
		org = p.get('organization')
		if org:
			r = r.filter(organization=org)
		it = p.get('item')
		if it:
			r = r.filter(item=it)

		#result
		j = []
		for i in r:
			j.append({"id": i.id, "str": str(i)})
		return HttpResponse(json.dumps(j))

# Split list that build upon this account is displayed
class AccountDetailView(ListView):
	model = Split
	paginate_by = 20

	def __get_object(self):
		self.object = Account.objects.get(uuid=self.kwargs['uuid'])

	def get_template_names(self):
		return ["%s/account_detail.html" % (Account._meta.app_label)]

	def get_queryset(self):
		self.__get_object()
		return Split.objects.filter(account=self.object).order_by("-transaction__time", "-transaction__id", "-id")

	def get_context_data(self, **kwargs):
		context = super(AccountDetailView, self).get_context_data(**kwargs)

		#object
		context['object'] = self.object
		self.object.lock = False
		if Split.objects.filter(account=self.object).exists():
			self.object.lock = True

		#balance
		balance = self.object.balance
		page = context['page_obj']
		total = self.get_queryset()[:self.paginate_by * (page.number - 1)].aggregate(Sum("change"))['change__sum']
		if not total:
			total = 0
		balance -= total
		for s in context["object_list"]:
			s.time = s.transaction.time.astimezone(timezone.get_current_timezone()).strftime("%Y-%m-%d %H:%M:%S")
			s.balance = balance
			balance -= s.change
			tr = s.transaction
			tsk = tr.task
			d = ""
			if tsk:
				d += tsk.desc
				o = None
				if Jdorder.objects.filter(pk=tsk.id).exists():
					o = Jdorder.objects.get(pk=tsk.id)
				if Tmorder.objects.filter(pk=tsk.id).exists():
					o = Tmorder.objects.get(pk=tsk.id)
				if o:
					d += "." + str(o.oid)
				d += "." + tr.desc
			else:
				d = tr.desc
			s.desc = d
			s.counters = s.transaction.splits.exclude(id=s.id)

		return context

class AccountDetailViewRead(AccountDetailView):
	def get_template_names(self):
		return ["%s/account_detail_read.html" % (Account._meta.app_label)]

class AccountDeleteView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		return reverse('chore_list')

	def get(self, request, *args, **kwargs):
		a = Account.objects.get(uuid=kwargs['uuid'])
		if not Split.objects.filter(account=a).exists():
			a.delete()
		return super(AccountDeleteView, self).get(request, *args, **kwargs)

class AccountReportView(SecurityLoginRequiredMixin, DetailView):
	model = Account
	slug_field = 'uuid'
	slug_url_kwarg = 'uuid'

	def get_template_names(self):
		return ['vault/account_report.html']

	def get_context_data(self, **kwargs):
		context = super(AccountReportView, self).get_context_data(**kwargs)

		result = []
		e = begin_of_month()
		b = nth_previous_month(e, 3)
		while True:
			_e = next_month(b)
			if _e > e:
				break
			q = Split.objects.filter(account=self.object)
			q = q.filter(transaction__time__gte=(b)).filter(transaction__time__lt=_e)
			income = float(get_decimal_with_default(q.filter(change__gte=0).aggregate(Sum('change'))['change__sum'], 0))
			expenditure = float(get_decimal_with_default(q.filter(change__lte=0).aggregate(Sum('change'))['change__sum'], 0))
			net = income + expenditure
			result.insert(0, [b, income, expenditure, net])
			b = _e
		context['reports'] = result

		return context
