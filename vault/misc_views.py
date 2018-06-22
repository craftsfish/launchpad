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

class RetailForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	sale = forms.DecimalField(initial=0, max_digits=20, decimal_places=2)

class ChangeForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)

class CommodityShippingBaseForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	keyword = forms.CharField()

class CommodityShippingForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status = forms.ChoiceField(choices=Itemstatus.choices)
	keyword = forms.CharField()

class CommodityChangeRepositoryForm(forms.Form):
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_f = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.RadioSelect, initial=0)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_t = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.RadioSelect, initial=0)
	keyword = forms.CharField()

class CommodityDetailBaseForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	repository = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
CommodityDetailBaseFormSet = formset_factory(CommodityDetailBaseForm, extra=0)

class CommodityDetailForm(CommodityDetailBaseForm):
	status = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
CommodityDetailFormSet = formset_factory(CommodityDetailForm, extra=0)

class CommodityChangeRepositoryDetailForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_f = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_t = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
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
			print form.errors
			print formset.errors
			return self.render_to_response(self.get_context_data(form=form, formset=formset))

class DailyTaskView(TemplateView):
	template_name = "{}/daily_task.html".format(Organization._meta.app_label)

class RetailView(FfsMixin, TemplateView):
	template_name = "{}/retail.html".format(Organization._meta.app_label)
	form_class = RetailForm
	formset_class = CommodityDetailBaseFormSet
	sub_form_class = CommodityShippingBaseForm

	def data_valid(self, form, formset):
		self.task = Task(desc="销售")
		self.task.save()
		t = timezone.now()
		self.org = form.cleaned_data['organization']
		self.sale = form.cleaned_data['sale']
		v = 0
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			r = d['repository']
			Transaction.add_raw(self.task, "出货", t, self.org, c.item_ptr, ("资产", "完好", r), -q, ("支出", "出货", r))
			v += q * c.value
		if self.sale == 0:
			self.sale = v
		cash = Money.objects.get(name="人民币")
		Transaction.add_raw(self.task, "货款", t, self.org, cash.item_ptr, ("资产", "应收货款", None), self.sale, ("收入", "销售收入", None))
		return super(RetailView, self).data_valid(form, formset)

class ChangeView(FfsMixin, TemplateView):
	template_name = "{}/change.html".format(Organization._meta.app_label)
	form_class = ChangeForm
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
			if q > 0:
				Transaction.add_raw(self.task, "换货.收货", t, o, c.item_ptr, ("资产", s, r), q, ("支出", "出货", r))
			else:
				Transaction.add_raw(self.task, "换货.发货", t, o, c.item_ptr, ("资产", s, r), q, ("支出", "出货", r))
		return super(ChangeView, self).data_valid(form, formset)

class ChangeRepositoryView(FfsMixin, TemplateView):
	template_name = "{}/change_repository.html".format(Organization._meta.app_label)
	form_class = ChangeForm
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

class PurchaseForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	repository = forms.ModelChoiceField(queryset=Repository.objects)

class PurchaseCommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	repository = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput, required=False)
	level = forms.IntegerField(required=False, widget=forms.HiddenInput)
PurchaseCommodityFormSet = formset_factory(PurchaseCommodityForm, extra=0)

class PurchaseFilterForm(forms.Form):
	keyword = forms.CharField()

class PurchaseMixin(FfsMixin):
	template_name = "{}/purchase.html".format(Organization._meta.app_label)
	form_class = PurchaseForm
	formset_class = PurchaseCommodityFormSet
	sub_form_class = PurchaseFilterForm

	def get_formset_initial(self):
		r = []
		for c in Turbine.replenish(self.get_supplier()):
			for repo, level, refill in c.detail:
				r.append({'id': c.id, 'quantity': int(refill), 'repository': repo, 'check': False, 'level': int(level)})
		return r

	def get_context_data(self, **kwargs):
		context = super(PurchaseMixin, self).get_context_data(**kwargs)
		for form in context['formset']:
			cid = form['id'].value()
			c = Commodity.objects.get(pk=cid)
			rid = form['repository'].value()
			r = Repository.objects.get(pk=rid)
			form.label = c.name
			form.note = "{}库存天数: {}".format(r.name, form['level'].value())
		return context

	def data_valid(self, form, formset):
		self.task = Task(desc="进货")
		self.task.save()
		t = timezone.now()
		o = form.cleaned_data['organization']
		r = form.cleaned_data['repository']
		merged = {}
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			q = d['quantity']
			if not q: continue
			c = d['id']
			if merged.get(c) != None:
				merged[c] += q
			else:
				merged[c] = q
		for cid, q in merged.items():
			c = Commodity.objects.get(pk=cid)
			Transaction.add_raw(self.task, "进货", t, o, c.item_ptr, ("资产", "应收", r), q, ("收入", "进货", r))
			cash = Money.objects.get(name="人民币")
			Transaction.add_raw(self.task, "货款", t, o, cash.item_ptr, ("负债", "应付货款", None), q*c.value, ("支出", "进货", None))
		return super(PurchaseMixin, self).data_valid(form, formset)

class TfgPurchaseView(PurchaseMixin, TemplateView):
	def get_supplier(self):
		return Supplier.objects.get(name="泰福高")

class YstPurchaseView(PurchaseMixin, TemplateView):
	def get_supplier(self):
		return Supplier.objects.get(name="原森太")

class KmlPurchaseView(PurchaseMixin, TemplateView):
	def get_supplier(self):
		return Supplier.objects.get(name="凯曼隆")

class OtherPurchaseView(PurchaseMixin, TemplateView):
	def get_supplier(self):
		return None

class AppendPurchaseForm(forms.Form):
	task = forms.IntegerField()
	organization = forms.ModelChoiceField(queryset=Organization.objects)
	repository = forms.ModelChoiceField(queryset=Repository.objects)

class AppendPurchaseView(FfsMixin, TemplateView):
	template_name = "{}/purchase.html".format(Organization._meta.app_label)
	form_class = AppendPurchaseForm
	formset_class = PurchaseCommodityFormSet
	sub_form_class = PurchaseFilterForm

	def data_valid(self, form, formset):
		try:
			self.task = Task.objects.get(pk=form.cleaned_data['task'])
		except Task.DoesNotExist as e:
			self.error = "任务不存在!"
			return self.render_to_response(self.get_context_data(form=form, formset=formset))
		t = timezone.now()
		o = form.cleaned_data['organization']
		r = form.cleaned_data['repository']
		merged = {}
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			q = d['quantity']
			if not q: continue
			c = d['id']
			if merged.get(c) != None:
				merged[c] += q
			else:
				merged[c] = q
		for cid, q in merged.items():
			c = Commodity.objects.get(pk=cid)
			Transaction.add_raw(self.task, "进货", t, o, c.item_ptr, ("资产", "应收", r), q, ("收入", "进货", r))
			cash = Money.objects.get(name="人民币")
			Transaction.add_raw(self.task, "货款", t, o, cash.item_ptr, ("负债", "应付货款", None), q*c.value, ("支出", "进货", None))
		return super(AppendPurchaseView, self).data_valid(form, formset)

class StorageCalibarionForm(forms.Form):
	check = forms.BooleanField()

class CommodityStorageCalibarionForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	in_book = forms.IntegerField(widget=forms.HiddenInput)
	q1 = forms.IntegerField(min_value=0, max_value=9999, required=False)
	q2 = forms.IntegerField(min_value=0, max_value=9999, required=False)
	q3 = forms.IntegerField(min_value=0, max_value=9999, required=False)
	q4 = forms.IntegerField(min_value=0, max_value=9999, required=False)
CommodityStorageCalibarionFormSet = formset_factory(CommodityStorageCalibarionForm, extra=0)

class DailyCalibrationView(FfsMixin, TemplateView):
	template_name = "{}/daily_calibration.html".format(Organization._meta.app_label)
	form_class = StorageCalibarionForm
	formset_class = CommodityStorageCalibarionFormSet
	sub_form_class = EmptyForm

	def get_formset_initial(self):
		d = []
		for c in Commodity.objects.order_by("calibration", "supplier", "name")[:15]:
			r = Repository.objects.get(name="孤山仓")
			v = Account.objects.filter(item=c).filter(repository=r).filter(name="完好").aggregate(Sum('balance'))['balance__sum']
			if v: v = int(v)
			else: v = 0
			d.append({'id': c.id, 'in_book': v})
		return d

	def get_context_data(self, **kwargs):
		context = super(DailyCalibrationView, self).get_context_data(**kwargs)
		for form in context['formset']:
			cid = form['id'].value()
			c = Commodity.objects.get(pk=cid)
			form.label = c.name
			form.label_in_book = form['in_book'].value()
		return context

	def dispatch(self, request, *args, **kwargs):
		self.error = None
		c = Commodity.objects.get(name="虚拟物品")
		if datetime.now(timezone.utc) > c.calibration:
			self.error = "已过盘点有效时间，请明天盘点"
			return self.render_to_response(self.get_context_data())
		return super(FfsMixin, self).dispatch(request, *args, **kwargs)

	def data_valid(self, form, formset):
		c = Commodity.objects.get(name="虚拟物品")
		if datetime.now(timezone.utc) > c.calibration:
			self.error = "已过盘点有效时间，请明天盘点"
			return self.render_to_response(self.get_context_data(form=form, formset=formset))
		self.task = None
		for f in formset:
			d = f.cleaned_data
			c = Commodity.objects.get(pk=d['id'])
			t = 0
			for i in range(4):
				t += get_int_with_default(d.get("q{}".format(i+1)), 0)
			self.task = Turbine.calibration_commodity(self.task, c, Repository.objects.get(name="孤山仓"), "完好", t,
				Organization.objects.filter(parent=None).exclude(name="个人"))
		return super(DailyCalibrationView, self).data_valid(form, formset)

	def get_success_url(self):
		if self.task:
			return reverse('task_detail_read', kwargs={'pk': self.task.id})
		else:
			return reverse('chore_list')

class OperationAccountClearForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects.exclude(name="个人"), label='收支主体')
	wallet = forms.ModelChoiceField(queryset=Wallet.objects.filter(name__startswith="运营资金"), label='账户')
	change = forms.DecimalField(initial=0, max_digits=20, decimal_places=2, label="变动金额")
	desc = forms.CharField(label='描述')

class OperationAccountClearView(FormView):
	template_name = "{}/operation_account_clear.html".format(Organization._meta.app_label)
	form_class = OperationAccountClearForm

	def form_valid(self, form):
		o = form.cleaned_data['organization']
		w = form.cleaned_data['wallet']
		c = form.cleaned_data['change']
		d = form.cleaned_data['desc']
		cash = Money.objects.get(name="人民币")
		a = Account.get(o.root(), cash.item_ptr, "资产", w.name, None)
		if c < 0:
			b = Account.get(o, cash.item_ptr, "支出", "其他支出", None)
		else:
			b = Account.get(o, cash.item_ptr, "收入", "其他收入", None)
		Transaction.add(None, d, timezone.now(), a, c, b)
		self.wallet = w
		return super(OperationAccountClearView, self).form_valid(form)

	def get_success_url(self):
		return reverse('wallet_detail', kwargs={'pk': self.wallet.id})
