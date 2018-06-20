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

class TaskListView(ListView):
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

class TaskDetailView(DetailView):
	model = Task

	def get_context_data(self, **kwargs):
		context = super(TaskDetailView, self).get_context_data(**kwargs)
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

		if Jdorder.objects.filter(pk=self.object.id).exists():
			context['order'] = Jdorder.objects.get(pk=self.object.id)
		if Tmorder.objects.filter(pk=self.object.id).exists():
			context['order'] = Tmorder.objects.get(pk=self.object.id)

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
		return reverse('task_detail', kwargs={'pk': self.prev.id})

	def get(self, request, *args, **kwargs):
		i = kwargs['pk']
		self.prev = Task.objects.filter(id__lt=i).order_by("id").last()
		if not self.prev:
			self.prev = Task.objects.get(id=i)
		return super(TaskPreviousView, self).get(request, *args, **kwargs)

class TaskNextView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		return reverse('task_detail', kwargs={'pk': self.next.id})

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
