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

class BuyFutureForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	repository = forms.ModelChoiceField(queryset=Repository.objects, required=False)

class CommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	name = forms.CharField(max_length=30, disabled=True, required=False)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	suggest_by = forms.CharField(max_length=30, disabled=True, required=False)
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
			{'id': it.id, 'name': it.name, 'quantity':8, 'check': True, 'suggest_by': 'Repository_A'},
		]
		for c in Commodity.objects.all():
			formset_initial.append({'id': c.id, 'name': c.name, 'quantity': 1, 'check': False, 'suggest_by': None})
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

class TaskReceiveFutureView(FormView):
	template_name = "{}/receive_future.html".format(Organization._meta.app_label)
	form_class = ReceiveForm

	def post(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['pk'])
		p = self.request.POST
		o = Organization.objects.get(pk=p['organization'])
		r = Organization.objects.get(pk=p['repository'])
		s = ReceiveForm.status_2_str(int(p.get('status')))
		for i in range(int(p['items_total'])):
			if p.get("invoice_{}_include".format(i)) == "on":
				it = Item.objects.get(pk=p["invoice_{}_item".format(i)])
				q = int(p["invoice_{}_quantity".format(i)])
				t = timezone.now()
				self.task.add_transaction("收货", t, o, it, ("资产", "应收"), -q, ("资产", "在库"))
				self.task.add_transaction("入库", t, r, it, ("资产", s), q, ("收入", "收货"))
		self.task.update()
		return super(TaskReceiveFutureView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['pk'])
		self.candidate_org = None
		self.candidates = {}
		for k, v in self.task.unreceived_accounts().items():
			a = Account.objects.get(pk=k)
			if a.item.id == Item.objects.get(name="人民币").id:
				continue
			if self.candidate_org == None:
				self.candidate_org = a.organization
			if a.organization == self.candidate_org:
				self.candidates[a.item.id] = v
		return super(TaskReceiveFutureView, self).get(request, *args, **kwargs)

	def get_initial(self):
		kwargs = super(TaskReceiveFutureView, self).get_initial()
		if self.request.method == 'GET':
			kwargs['organization'] = self.candidate_org
		return kwargs

	def get_context_data(self, **kwargs):
		context = super(TaskReceiveFutureView, self).get_context_data(**kwargs)

		context['items'] = Item.objects.all()
		for i, j in enumerate(context['items']):
			j.name_check = "invoice_{}_include".format(i)
			j.name_item = "invoice_{}_item".format(i)
			j.name_quantity = "invoice_{}_quantity".format(i)
			j.step = 1
			j.quantity = 1
			j.checked = ""
			if self.candidates.has_key(j.id):
				j.checked = "checked"
				j.quantity = int(self.candidates[j.id])

		return context
