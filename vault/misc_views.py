# -*- coding: utf-8 -*-
from django.views.generic import TemplateView
from .models import *
from organization import *
from django import forms
from turbine import *
from django.forms import formset_factory
from django.views.generic import FormView
from django.views.generic.base import ContextMixin
from django.http import HttpResponseRedirect
from django.utils import timezone
from .base_forms import *

class CommodityShippingBaseForm(BaseKeywordForm, BaseRepositoryForm): pass

class CommodityShippingForm(BaseKeywordForm, BaseCommodityStatusForm, BaseShipStatusForm, BaseRepositoryForm): pass

class CommodityReceiveForm(BaseKeywordForm, BaseCommodityStatusForm, BaseShipStatusReceiveForm, BaseRepositoryForm): pass

class CommoditySendForm(BaseKeywordForm, BaseCommodityStatusForm, BaseShipStatusSendForm, BaseRepositoryForm): pass

class CommodityChangeRepositoryForm(BaseKeywordForm, BaseRepositoryChangeForm): pass

class CommodityDetailBaseForm(BaseRepositoryHiddenForm, BaseCommodityDetailForm): pass
CommodityDetailBaseFormSet = formset_factory(CommodityDetailBaseForm, extra=0)

class CommodityDetailForm(BaseShipStatusHiddenForm, BaseCommodityStatusHiddenForm, CommodityDetailBaseForm): pass
CommodityDetailFormSet = formset_factory(CommodityDetailForm, extra=0)

class CommodityChangeRepositoryDetailForm(BaseRepositoryChangeHiddenForm, BaseCommodityDetailForm): pass
CommodityChangeRepositoryDetailFormSet = formset_factory(CommodityChangeRepositoryDetailForm, extra=0)

class FfsMixin(ContextMixin):
	"""
	A mixin that provides a way to show and handle form + formset in a request.
	"""
	form_class = None
	formset_class = None
	sub_form_class = None

	def get_formset_initial(self):
		return []

	def dispatch(self, request, *args, **kwargs):
		self.error = None
		return super(FfsMixin, self).dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		if 'form' not in kwargs:
			kwargs['form'] = self.form_class()
		if 'sub_form' not in kwargs and self.sub_form_class:
			kwargs['sub_form'] = self.sub_form_class()
		if 'formset' not in kwargs:
			kwargs['formset'] = self.formset_class(initial=self.get_formset_initial(), auto_id=False)
		if 'error' not in kwargs:
			kwargs['error'] = self.error
		return super(FfsMixin, self).get_context_data(**kwargs)

	def get_success_url(self):
		return reverse('task_detail_read', kwargs={'pk': self.task.id})

	def data_valid(self, form, formset):
		return HttpResponseRedirect(self.get_success_url())

	def post(self, request, *args, **kwargs):
		form = self.form_class(self.request.POST)
		formset = self.formset_class(self.request.POST)
		if form.is_valid() and formset.is_valid():
			return self.data_valid(form, formset)
		else:
			return self.render_to_response(self.get_context_data(form=form, formset=self.formset_class()))

class DailyTaskView(TemplateView):
	template_name = "{}/daily_task.html".format(Organization._meta.app_label)

class RetailView(FfsMixin, TemplateView):
	template_name = "{}/retail.html".format(Organization._meta.app_label)
	form_class = BaseIndividualForm
	formset_class = CommodityDetailBaseFormSet
	sub_form_class = CommodityShippingBaseForm

	def data_valid(self, form, formset):
		self.task = Task(desc="销售")
		self.task.save()
		cash = Money.objects.get(name="人民币")
		t = timezone.now()
		self.org = form.cleaned_data['organization']
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			r = d['repository']
			Transaction.add_raw(self.task, "出货", t, self.org, c.item_ptr, ("资产", "完好", r), -q, ("支出", "出货", r))
			Transaction.add_raw(self.task, "货款", t, self.org, cash.item_ptr, ("资产", "应收货款", None), q * c.value, ("收入", "销售收入", None))
		return super(RetailView, self).data_valid(form, formset)

class ChangeView(FfsMixin, TemplateView):
	template_name = "{}/change.html".format(Organization._meta.app_label)
	form_class = BaseOrganizationForm
	formset_class = CommodityDetailFormSet
	sub_form_class = CommodityShippingForm

	def data_valid(self, form, formset):
		self.task = Task(desc="换货")
		self.task.save()
		t = timezone.now()
		o = form.cleaned_data['organization']
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			if not q: continue
			r = d['repository']
			s = Itemstatus.v2s(d['status'])
			ship = Shipstatus.v2s(d['ship'])
			if ship == "收货":
				Transaction.add_raw(self.task, "换货.收货", t, o, c.item_ptr, ("资产", s, r), q, ("支出", "出货", r))
			else:
				Transaction.add_raw(self.task, "换货.发货", t, o, c.item_ptr, ("资产", s, r), -q, ("支出", "出货", r))
		return super(ChangeView, self).data_valid(form, formset)

class ChangeRepositoryView(FfsMixin, TemplateView):
	template_name = "{}/change_repository.html".format(Organization._meta.app_label)
	form_class = BaseOrganizationForm
	formset_class = CommodityChangeRepositoryDetailFormSet
	sub_form_class = CommodityChangeRepositoryForm

	def data_valid(self, form, formset):
		self.task = Task(desc="换仓")
		self.task.save()
		t = timezone.now()
		o = form.cleaned_data['organization']
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			if not q: continue
			rf = d['repository_f']
			sf = Itemstatus.v2s(d['status_f'])
			rt = d['repository_t']
			st = Itemstatus.v2s(d['status_t'])
			Transaction.add_raw(self.task, "换仓", t, o, c.item_ptr, ("资产", sf, rf), -q, ("资产", st, rt))
		return super(ChangeRepositoryView, self).data_valid(form, formset)

class ReceivableCommodityView(TemplateView):
	template_name = "{}/receivable_commodity.html".format(Organization._meta.app_label)

	def get_context_data(self, **kwargs):
		context = super(ReceivableCommodityView, self).get_context_data(**kwargs)
		l = []
		for i in Account.objects.filter(name="应收").exclude(balance=0).values_list('item', flat=True).distinct():
			if Commodity.objects.filter(pk=i).exists():
				c = Commodity.objects.get(pk=i)
				c.accounts = Account.objects.filter(name="应收").filter(item=c).exclude(balance=0).order_by('organization')
				c.total = 0
				for a in c.accounts:
					c.total += a.balance
				l.append(c)
				print c
		def __key(c):
			if c.supplier:
				return "{}-{}".format(c.supplier.id, c.name)
			else:
				return "None-{}".format(c.name)
		context['object_list'] = sorted(l, key=__key)
		return context

class OperationAccountClearForm(forms.Form):
	task = forms.IntegerField(required=False, label='(可选)关联到指定任务')
	organization = forms.ModelChoiceField(queryset=Organization.objects.exclude(name="个人"), label='收支主体')
	wallet = forms.ModelChoiceField(queryset=Wallet.objects.filter(name__startswith="运营资金"), label='账户')
	change = forms.DecimalField(initial=0, max_digits=20, decimal_places=2, label="变动金额")
	desc = forms.CharField(label='描述')

	def clean(self):
		cleaned_data = super(OperationAccountClearForm, self).clean()
		task_id = cleaned_data.get("task")
		if task_id:
			if not Task.objects.filter(id=task_id).exists():
				raise forms.ValidationError("非法任务编号")

class OperationAccountClearView(FormView):
	template_name = "{}/operation_account_clear.html".format(Organization._meta.app_label)
	form_class = OperationAccountClearForm

	def form_valid(self, form):
		self.task = None
		t = form.cleaned_data['task']
		if t:
			self.task = Task.objects.get(id=t)
		o = form.cleaned_data['organization']
		w = form.cleaned_data['wallet']
		c = form.cleaned_data['change']
		d = form.cleaned_data['desc']
		cash = Money.objects.get(name="人民币")
		a = Account.get(o.root(), cash.item_ptr, "资产", w.name, None)
		if c < 0:
			b = Account.get_or_create(o, cash.item_ptr, "支出", "其他支出", None)
		else:
			b = Account.get_or_create(o, cash.item_ptr, "收入", "其他收入", None)
		Transaction.add(self.task, d, timezone.now(), a, c, b)
		self.wallet = w
		return super(OperationAccountClearView, self).form_valid(form)

	def get_success_url(self):
		if self.task:
			return reverse('task_detail_read', kwargs={'pk': self.task.id})
		else:
			return reverse('wallet_detail', kwargs={'pk': self.wallet.id})

class PayWechatRecruitBonusForm(forms.Form):
	wallet = forms.ModelChoiceField(queryset=Wallet.objects.filter(name__startswith="运营资金"), label='付款账户')
	change = forms.DecimalField(initial=0, max_digits=20, decimal_places=2, min_value=0.01, label="支付金额")

class PayWechatRecruitBonusView(FormView):
	template_name = "base_form.html"
	form_class = PayWechatRecruitBonusForm

	def form_valid(self, form):
		o = Organization.objects.get(name="南京为绿电子科技有限公司")
		w = form.cleaned_data['wallet']
		c = form.cleaned_data['change']
		cash = Money.objects.get(name="人民币")
		a = Account.get(o, cash.item_ptr, "资产", w.name, None)
		b = Account.get_or_create(o, cash.item_ptr, "支出", "其他支出", None)
		Transaction.add(None, "微信拉人", timezone.now(), a, -c, b)
		self.wallet = w
		return super(PayWechatRecruitBonusView, self).form_valid(form)

	def get_success_url(self):
		return reverse('wallet_detail', kwargs={'pk': self.wallet.id})

	def get_context_data(self, **kwargs):
		kwargs['title'] = "支付微信刷单拉人奖励"
		return super(PayWechatRecruitBonusView, self).get_context_data(**kwargs)

class HelpView(TemplateView):
	template_name = "{}/help.html".format(Organization._meta.app_label)
