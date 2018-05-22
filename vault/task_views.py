# -*- coding: utf-8 -*-
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import RedirectView
from django import forms
from django.views.generic import FormView
from django.utils import timezone
from task import *

class TaskListView(ListView):
	model = Task

class TaskDetailView(DetailView):
	model = Task

	def get_context_data(self, **kwargs):
		context = super(TaskDetailView, self).get_context_data(**kwargs)
		context['trans'] = self.object.transactions.all().order_by("time", "id")
		max_splits = 0
		for t in context['trans']:
			t.ss = t.splits.all().order_by("id")
			if len(t.ss) > max_splits:
				max_splits = len(t.ss)
		context['detail_spans'] = max_splits * 2
		return context

class TaskDeleteView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		return reverse('task_list')

	def get(self, request, *args, **kwargs):
		Task.objects.get(pk=kwargs['pk']).delete()
		return super(TaskDeleteView, self).get(request, *args, **kwargs)

class EnterpriseForm(forms.Form):
	os = []
	o = Organization.objects.get(name="企业")
	for i in o.descendants():
		os.append(i.id)
	organization = forms.ModelChoiceField(queryset=Organization.objects.filter(id__in=os))

class TaskBuyFutureView(FormView):
	template_name = "{}/buy_future.html".format(Organization._meta.app_label)
	form_class = EnterpriseForm

	def post(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['pk'])
		p = self.request.POST
		o = Organization.objects.get(pk=p['organization'])
		for i in range(int(p['items_total'])):
			if p.get("invoice_{}_include".format(i)) == "on":
				it = Item.objects.get(pk=p["invoice_{}_item".format(i)])
				q = int(p["invoice_{}_quantity".format(i)])
				cash = Item.objects.get(name="人民币")
				t = timezone.now()
				self.task.add_transaction("进货.{}".format(it.name), t, o, it, ("资产", "应收"), q, ("收入", "进货"))
				self.task.add_transaction("货款.{}".format(it.name), t, o, cash, ("负债", "应付货款"), q*it.value, ("支出", "进货"))
		return super(TaskBuyFutureView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(TaskBuyFutureView, self).get_context_data(**kwargs)
		context['items'] = Item.objects.all()
		for i, j in enumerate(context['items']):
			j.name_check = "invoice_{}_include".format(i)
			j.name_item = "invoice_{}_item".format(i)
			j.name_quantity = "invoice_{}_quantity".format(i)
			j.step = 3
		return context
