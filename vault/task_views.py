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
from turbine import *
from .security import *

class TaskListView(SecurityLoginRequiredMixin, ListView):
	model = Task
	paginate_by = 50

	def get_queryset(self):
		return Task.objects.order_by("-id")

	def get_context_data(self, **kwargs):
		context = super(TaskListView, self).get_context_data(**kwargs)
		for t in context['object_list']:
			t.start = t.transactions.order_by("time").values_list('time', flat=True).first()
			t.end = t.transactions.order_by("time").values_list('time', flat=True).last()
		return context

class TaskDetailView(SecurityLoginRequiredMixin, DetailView):
	model = Task

	def get_context_data(self, **kwargs):
		context = super(TaskDetailView, self).get_context_data(**kwargs)

		context['expresses'] = self.object.express_set.all()

		m = [] #for currency accounts
		c = [] #for commodity accounts
		for k, v in self.object.uncleared_accounts().items():
			a = Account.objects.get(pk=k)
			if Commodity.objects.filter(pk=a.item.id).exists():
				c.append([a, v, Commodity.objects.get(pk=a.item.id)])
			else:
				m.append([a, v])
		context['uncleared'] = m
		def __key(i):
			if i[2].supplier:
				return i[2].supplier.name + i[2].name
			else:
				return "None" + i[2].name
		c.sort(key=__key)
		for i in c:
			i.pop()
		context['unsettled'] = c

		context['trans'] = self.object.transactions.all().order_by("time", "id")
		max_splits = 0
		for t in context['trans']:
			t.ss = t.splits.all().order_by("id")
			t.is_money = Money.objects.filter(pk=t.ss[0].account.item.id).exists()
			if len(t.ss) > max_splits:
				max_splits = len(t.ss)
		context['detail_spans'] = max_splits * 2

		order = None
		if hasattr(self.object, "jdorder"):
			order = Jdorder.objects.get(pk=self.object.id)
		if hasattr(self.object, "tmorder"):
			order = Tmorder.objects.get(pk=self.object.id)
		if order:
			remark = ""
			for i in order.task_ptr.transactions.filter(desc="刷单.发货").order_by("id"):
				split = i.splits.order_by("account__category", "change").last()
				if remark != "":
					remark += ", "
				remark += "{}: {:+.0f}".format(split.account.item.name, split.change)
			context['order'] = order
			context['remark'] = "邓丽君: {" + remark + "}"

		return context

class TaskDetailViewRead(TaskDetailView):
	template_name = "{}/task_detail_read.html".format(Organization._meta.app_label)

class TaskDeleteView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		return reverse('task_list')

	def get(self, request, *args, **kwargs):
		Task.objects.get(pk=kwargs['pk']).delete()
		return super(TaskDeleteView, self).get(request, *args, **kwargs)

class TaskPreviousView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		return reverse('task_detail_read', kwargs={'pk': self.prev.id})

	def get(self, request, *args, **kwargs):
		i = kwargs['pk']
		self.prev = Task.objects.filter(id__lt=i).order_by("id").last()
		if not self.prev:
			self.prev = Task.objects.get(id=i)
		return super(TaskPreviousView, self).get(request, *args, **kwargs)

class TaskNextView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		return reverse('task_detail_read', kwargs={'pk': self.next.id})

	def get(self, request, *args, **kwargs):
		i = kwargs['pk']
		self.next = Task.objects.filter(id__gt=i).order_by("id").first()
		if not self.next:
			self.next = Task.objects.get(id=i)
		return super(TaskNextView, self).get(request, *args, **kwargs)

class TaskClearForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	item = forms.ModelChoiceField(queryset=Money.objects, empty_label=None)

class TaskClearAccountForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	change = forms.DecimalField(max_digits=20, decimal_places=2)
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
	status = forms.ChoiceField(choices=Itemstatus.choices[1:4])
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
			b = Account.get_or_create(o, a.item, "资产", Itemstatus.v2s(n), r)
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

class TaskClearBillForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects.filter(parent=None), label="主体")
	wallet = forms.ModelChoiceField(queryset=Wallet.objects.filter(name__startswith="运营资金"), label='账户')
	status = forms.ChoiceField(choices=ClearStatus.choices, label="收/付款")
	amount = forms.DecimalField(initial=0, max_digits=10, decimal_places=2, min_value=0.01, label="金额")

class TaskClearBillView(FormView):
	template_name = "base_form.html"
	form_class = TaskClearBillForm

	def form_valid(self, form):
		o = form.cleaned_data['organization']
		w = form.cleaned_data['wallet']
		s = form.cleaned_data['status']
		q = form.cleaned_data['amount']
		cash = Money.objects.get(name="人民币")
		a = Account.get(o.root(), cash.item_ptr, "资产", w.name, None)
		if ClearStatus.v2s(s) == "收款":
			b = Account.get_or_create(o, cash.item_ptr, "资产", "应收货款", None)
		else:
			q = -q
			b = Account.get_or_create(o, cash.item_ptr, "负债", "应付货款", None)
		Transaction.add(self.task, "结算", timezone.now(), a, q, b)
		return super(TaskClearBillView, self).form_valid(form)

	def get_success_url(self):
		return reverse('task_detail_read', kwargs={'pk': self.task.id})

	def dispatch(self, request, *args, **kwargs):
		self.task = Task.objects.get(pk=kwargs['pk'])
		return super(TaskClearBillView, self).dispatch(request, *args, **kwargs)

class TaskInvoiceView(DetailView):
	model = Task
	template_name = "{}/task_invoices.html".format(Organization._meta.app_label)

	def get_context_data(self, **kwargs):
		context = super(TaskInvoiceView, self).get_context_data(**kwargs)
		order = None
		if hasattr(self.object, "jdorder"):
			order = self.object.jdorder
		if hasattr(self.object, "tmorder"):
			order = self.object.tmorder
		if not order: return context

		context['order'] = order
		invoices = []
		for i in order.task_ptr.transactions.filter(desc="刷单.发货").order_by("id"):
			invoices.append(i.splits.order_by("account__category", "change").last())
		context['invoices'] = invoices
		return context

class TaskRevertView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		return reverse('task_detail', kwargs={'pk': self.object.id})

	def get(self, request, *args, **kwargs):
		self.object = Task.objects.get(pk=kwargs['pk'])
		for i in self.object.transactions.order_by("id"):
			args = []
			for s in i.splits.order_by("id"):
				args.append(s.account)
				args.append(-s.change)
			Transaction.add(self.object, "取消", timezone.now(), *args)
		return super(TaskRevertView, self).get(request, *args, **kwargs)
