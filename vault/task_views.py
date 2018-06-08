# -*- coding: utf-8 -*-
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import RedirectView
from django import forms
from django.forms import formset_factory
from django.views.generic import FormView
from django.utils import timezone
from task import *

class TaskListView(ListView):
	model = Task

	def get_queryset(self):
		return Task.objects.order_by("-id")

	def get_context_data(self, **kwargs):
		context = super(TaskListView, self).get_context_data(**kwargs)
		for t in context['object_list']:
			t.start = t.transactions.order_by("time").values_list('time', flat=True).first()
			t.end = t.transactions.order_by("time").values_list('time', flat=True).last()
		return context

class TaskDetailView(DetailView):
	model = Task

	def get_context_data(self, **kwargs):
		context = super(TaskDetailView, self).get_context_data(**kwargs)
		context['items'] = Item.objects.all()
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

class BuyFutureForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	repository = forms.ModelChoiceField(queryset=Repository.objects, required=False)

class CommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	name = forms.CharField(max_length=30, disabled=True, required=False)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	repository = forms.CharField(max_length=30, disabled=True, required=False)
CommodityFormSet = formset_factory(CommodityForm, extra=0)

class TaskBuyFutureView(FormView):
	template_name = "{}/buy_future.html".format(Organization._meta.app_label)
	form_class = BuyFutureForm

	def post(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['pk'])
		p = self.request.POST
		o = Organization.objects.get(pk=p['organization'])
		r = None
		if p['repository'] != '':
			r = Repository.objects.get(pk=p['repository'])
		formset = CommodityFormSet(self.request.POST)
		merged = {}
		if formset.is_valid():
			for f in formset:
				d = f.cleaned_data
				if not d['check']:
					continue
				cid = d['id']
				if merged.get(cid):
					merged[cid] += d['quantity']
				else:
					merged[cid] = d['quantity']
		for cid, quantity in merged.items():
			c = Commodity.objects.get(pk=cid)
			t = timezone.now()
			cash = Money.objects.get(name="人民币")
			Transaction.add(self.task, "进货", t, o, c.item_ptr, ("资产", "应收", r), quantity, ("收入", "进货", r))
			Transaction.add(self.task, "货款", t, o, cash.item_ptr, ("负债", "应付货款", None), quantity*c.value, ("支出", "进货", None))

		return super(TaskBuyFutureView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(TaskBuyFutureView, self).get_context_data(**kwargs)
		it = Commodity.objects.all()[0] #TODO: replace with actual candidates
		formset_initial = [
			{'id': it.id, 'name': it.name, 'quantity':8, 'check': True, 'repository': 'Repository_A'},
		]
		for c in Commodity.objects.all():
			formset_initial.append({'id': c.id, 'name': c.name, 'quantity': 1, 'check': False, 'repository': None})
		context['formset'] = CommodityFormSet(initial = formset_initial)
		return context

class ReceiveForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	repository = forms.ModelChoiceField(queryset=Repository.objects)
	ITEM_STATUS_CHOICES = (
		(0, "完好"),
		(1, "残缺"),
		(2, "破损"),
	)
	status = forms.ChoiceField(choices=ITEM_STATUS_CHOICES)

	@staticmethod
	def status_2_str(s):
		for i, v in ReceiveForm.ITEM_STATUS_CHOICES:
			if i == s:
				return v
		return None

class ReceiveCommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	name = forms.CharField(max_length=30, disabled=True, required=False)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	organization = forms.CharField(max_length=30, disabled=True, required=False)
	repository = forms.CharField(max_length=30, disabled=True, required=False)
ReceiveCommodityFormSet = formset_factory(ReceiveCommodityForm, extra=0)

class TaskReceiveFutureView(FormView):
	template_name = "{}/receive_future.html".format(Organization._meta.app_label)
	form_class = ReceiveForm

	def post(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['pk'])
		form = ReceiveForm(self.request.POST)
		if form.is_valid():
			o = form.cleaned_data['organization']
			r = form.cleaned_data['repository']
			s = int(form.cleaned_data['status'])
		formset = ReceiveCommodityFormSet(self.request.POST)
		if formset.is_valid():
			for f in formset:
				d = f.cleaned_data
				if d['check']:
					a = Account.objects.get(pk = d['id'])
					t = timezone.now()
					Transaction.add(self.task, "入库", t, o, a.item,
						("资产", ReceiveForm.status_2_str(s), r), d['quantity'],
						(a.get_category_display(), a.name, a.repository))
		return super(TaskReceiveFutureView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['pk'])
		return super(TaskReceiveFutureView, self).get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(TaskReceiveFutureView, self).get_context_data(**kwargs)
		formset_initial = []
		for aid, balance in self.task.candidates_of_repository_in().items(): #TODO: sorted with organization & repository
			a = Account.objects.get(pk=aid)
			c = a.item
			formset_initial.append({'id': a.id, 'name': c.name, 'quantity': balance, 'check': False, 'organization': a.organization, 'repository': a.repository})
		context['formset'] = ReceiveCommodityFormSet(initial = formset_initial)
		return context
