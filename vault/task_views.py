# -*- coding: utf-8 -*-
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import RedirectView
from django import forms
from django.forms import formset_factory
from django.views.generic import FormView
from django.utils import timezone
from task import *
from .misc_views import *

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
		l = []
		for k, v in self.object.uncleared_accounts().items():
			l.append([Account.objects.get(pk=k), v])
		context['uncleared_list'] = l
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
			Transaction.add_raw(self.task, "进货", t, o, c.item_ptr, ("资产", "应收", r), quantity, ("收入", "进货", r))
			Transaction.add_raw(self.task, "货款", t, o, cash.item_ptr, ("负债", "应付货款", None), quantity*c.value, ("支出", "进货", None))

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

class EmptyForm(forms.Form):
	pass

class TaskClearForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	item = forms.ModelChoiceField(queryset=Money.objects, empty_label=None)

class TaskClearAccountForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	change = forms.IntegerField()
	check = forms.BooleanField(required=False)
TaskClearAccountFormSet = formset_factory(TaskClearAccountForm, extra=0)

class TaskClearView(FfsMixin, TemplateView):
	template_name = "{}/task_clear.html".format(Organization._meta.app_label)
	form_class = EmptyForm
	formset_class = TaskClearAccountFormSet
	sub_form_class = TaskClearForm

	def data_valid(self, form, formset):
		args = []
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			a = Account.objects.get(pk=d['id'])
			change = d['change']
			if not change: continue
			args.append(a)
			args.append(change)
		if Transaction.add(self.task, "结算", timezone.now(), *args):
			return super(TaskClearView, self).data_valid(form, formset)
		else:
			self.error = "交易不合法，请检查是否属于同一根组织或者帐目是否平衡!!!"
			return self.render_to_response(self.get_context_data(form=form, formset=formset))

	def dispatch(self, request, *args, **kwargs):
		self.error = None
		self.task = Task.objects.get(pk=kwargs['pk'])
		return super(TaskClearView, self).dispatch(request, *args, **kwargs)

	def get_formset_initial(self):
		r = []
		for aid, balance in self.task.uncleared_accounts().items():
			a = Account.objects.get(pk=aid)
			i = a.item
			if Money.objects.filter(pk=i.id).exists():
				r.append({'id': aid, 'change': -balance, 'check': False})
		return r

	def get_context_data(self, **kwargs):
		context = super(TaskClearView, self).get_context_data(**kwargs)
		for form in context['formset']:
			aid = form['id'].value()
			a = Account.objects.get(pk=aid)
			form.label = a.organization.name + ": " + str(a)
		context['error'] = self.error
		return context

class TaskSettleForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	repository = forms.ModelChoiceField(queryset=Repository.objects)
	status = forms.ChoiceField(choices=Itemstatus.choices)
	ship = forms.ChoiceField(choices=Shipstatus.choices)

class TaskSettleAccountForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
TaskSettleAccountFormSet = formset_factory(TaskSettleAccountForm, extra=0)

class TaskSettleView(FfsMixin, TemplateView):
	template_name = "{}/task_settle.html".format(Organization._meta.app_label)
	form_class = TaskSettleForm
	formset_class = TaskSettleAccountFormSet
	sub_form_class = EmptyForm

	def data_valid(self, form, formset):
		o = form.cleaned_data['organization']
		r = form.cleaned_data['repository']
		n = form.cleaned_data['status']
		s = int(form.cleaned_data['ship'])
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			a = Account.objects.get(pk=d['id'])
			q = d['quantity']
			if not q: continue
			if a.organization.id != o.id: continue
			if a.repository.id != r.id: continue
			if s == 0 and a.category != 0: continue
			if s == 1 and a.category != 1: continue
			b = Account.get(o, a.item, "资产", Itemstatus.v2s(n), r)
			if s:
				Transaction.add(self.task, "出库", timezone.now(), a, -q, b)
			else:
				Transaction.add(self.task, "入库", timezone.now(), a, -q, b)
		return super(TaskSettleView, self).data_valid(form, formset)

	def dispatch(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['pk'])
		return super(TaskSettleView, self).dispatch(request, *args, **kwargs)

	def get_formset_initial(self):
		r = []
		for aid, balance in self.task.uncleared_accounts().items():
			a = Account.objects.get(pk=aid)
			i = a.item
			if Commodity.objects.filter(pk=i.id).exists():
				r.append({'id': aid, 'quantity': balance, 'check': False})
		return r

	def get_context_data(self, **kwargs):
		context = super(TaskSettleView, self).get_context_data(**kwargs)
		for form in context['formset']:
			aid = form['id'].value()
			a = Account.objects.get(pk=aid)
			form.label = a.organization.name + " : " + a.item.name + " : " + str(a)
		return context
