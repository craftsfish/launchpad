# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.views.generic import ListView
from django.views.generic import RedirectView

class TransactionForm(forms.ModelForm):
	class Meta:
		model = Transaction
		fields = ['desc', 'time', 'task']
		widgets = {
			'time': forms.TextInput(attrs={"class": "form-control datetimepicker-input", "data-target": "#datetimepicker1", "data-toggle": "datetimepicker"}),
			'task': forms.NumberInput(),
		}

class TransactionMixin(object):
	model = Transaction
	form_class = TransactionForm

class TransactionListView(ListView):
	model = Transaction
	paginate_by = 20

class TransactionDetailView(DetailView):
	model = Transaction

	def get_context_data(self, **kwargs):
		context = super(TransactionDetailView, self).get_context_data(**kwargs)
		splits = self.object.splits.all()
		context['splits'] = splits
		context['organization'] = splits[0].account.organization
		context['item'] = splits[0].account.item
		return context

class AccountForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects.all(), required=False)

SplitFormSet = inlineformset_factory(Transaction, Split, fields=('change', 'account'), widgets = {'account': forms.HiddenInput()}, labels = {'change': ''}, extra=0)
class TransactionUpdateView(TransactionMixin, UpdateView):
	def get_context_data(self, **kwargs):
		context = super(TransactionUpdateView, self).get_context_data(**kwargs)
		context['formset'] = SplitFormSet(instance=self.object)
		for f in context['formset']:
			f.account_display_name = str(f.instance.account)
		context['item'] = Account.objects.get(pk=f['account'].value()).item
		context['account'] = AccountForm()
		context['error'] = self.error
		return context

	def form_valid(self, form):
		formset = SplitFormSet(self.request.POST, self.request.FILES, instance=self.object)
		if formset.is_valid():
			formset.save()

		#splits in same transaction must belongs to same root organization and balanced
		balance = 0
		ref_org = None
		for s in self.object.splits.all():
			o = s.account.organization
			if ref_org == None:
				ref_org = o.root()
			if o.root().id != ref_org.id:
				self.error = "错误: 账户不属于同一个组织!"
				return self.render_to_response(self.get_context_data(form=form))
			balance += s.account.sign() * s.change
		if balance != 0:
			self.error = "错误: 帐目不平衡!"
			return self.render_to_response(self.get_context_data(form=form))

		return super(TransactionUpdateView, self).form_valid(form)

	def dispatch(self, request, *args, **kwargs):
		self.error = None
		return super(TransactionUpdateView, self).dispatch(request, *args, **kwargs)

class TransactionDuplicateView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		f = Transaction.objects.get(pk=kwargs['pk'])
		t = Transaction(desc=f.desc, task=f.task, time=timezone.now())
		t.save()
		for s in f.splits.all():
			Split(account=s.account, change=s.change, transaction=t).save()
		return reverse('transaction_update', kwargs={'pk': t.id})

class TransactionDeleteView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		if self.task:
			return self.task.get_absolute_url()
		else:
			return reverse('transaction_list')

	def get(self, request, *args, **kwargs):
		t = Transaction.objects.get(pk=kwargs['pk'])
		self.task = t.task
		t.delete()
		return super(TransactionDeleteView, self).get(request, *args, **kwargs)

class TransactionRevertView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		t = Transaction.objects.get(pk=kwargs['pk'])
		return t.task.get_absolute_url()

	def get(self, request, *args, **kwargs):
		t = Transaction.objects.get(pk=kwargs['pk'])
		args = []
		for s in t.splits.order_by("id"):
			args.append(s.account)
			args.append(-s.change)
		Transaction.add(t.task, "取消", timezone.now(), *args)
		return super(TransactionRevertView, self).get(request, *args, **kwargs)
