# -*- coding: utf-8 -*-
from .misc_views import *
from django.utils import timezone
from django.views.generic import RedirectView
from .turbine import *
from .base_forms import *

class TmorderDetailViewRead(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		try:
			return reverse('task_detail_read', kwargs={'pk': Tmorder.objects.get(oid=kwargs['pk']).id})
		except Tmorder.DoesNotExist as e:
			return reverse('chore_list')

class TmorderMixin(FfsMixin):
	"""
	A mixin that provides a way to show and handle tmorder in a request.
	"""
	form_class = TmorderForm
	formset_class = CommodityDetailFormSet
	sub_form_class = CommodityShippingForm

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		pass

	def data_valid(self, form, formset):
		self.org = form.cleaned_data['organization']
		o = form.cleaned_data['tmorder']
		o, created = Tmorder.objects.get_or_create(oid=o, desc="天猫订单")
		self.task = o.task_ptr
		t = timezone.now()
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			if not q: continue
			r = d['repository']
			s = Itemstatus.v2s(d['status'])
			ship = Shipstatus.v2s(d['ship'])
			self.formset_item_process(t, c.item_ptr, q, r, s, ship)
		return super(TmorderMixin, self).data_valid(form, formset)

class TmorderChangeView(TmorderMixin, TemplateView):
	template_name = "{}/tmorder_change.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		if ship == "收货":
			Transaction.add_raw(self.task, "换货.收货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		else:
			Transaction.add_raw(self.task, "换货.发货", time, self.org, item, ("资产", status, repository), -quantity, ("支出", "出货", repository))
		return super(TmorderChangeView, self).formset_item_process(time, item, quantity, repository, status, ship)

class TmorderCompensateView(TmorderMixin, TemplateView):
	template_name = "{}/tmorder_compensate.html".format(Organization._meta.app_label)
	sub_form_class = CommoditySendForm

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		Transaction.add_raw(self.task, "补发", time, self.org, item, ("资产", status, repository), -quantity, ("支出", "出货", repository))
		return super(TmorderCompensateView, self).formset_item_process(time, item, quantity, repository, status, ship)

class TmorderReturnView(TmorderMixin, TemplateView):
	template_name = "{}/tmorder_return.html".format(Organization._meta.app_label)
	sub_form_class = CommodityReceiveForm

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		#when order information is synchronized, we will adjust the repository of deliver, now just use what user chose
		Transaction.add_raw(self.task, "退货", time, self.org, item, ("资产", status, repository), quantity, ("资产", "完好", repository))
		return super(TmorderReturnView, self).formset_item_process(time, item, quantity, repository, status, ship)

class TmorderWechatFakeView(FakeOrderCandidatesMixin, TmorderMixin, TemplateView):
	template_name = "{}/tmorder_wechat_fake.html".format(Organization._meta.app_label)
	sub_form_class = CommoditySendForm

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		o = self.task.tmorder
		o.counterfeit = Counterfeit.objects.get(name="微信")
		o.save()
		Transaction.add_raw(self.task, "刷单.发货", time, self.org, item, ("资产", status, repository), -quantity, ("支出", "出货", repository))
		return super(TmorderWechatFakeView, self).formset_item_process(time, item, quantity, repository, status, ship)

class TmorderRebateForm(TmorderForm):
	wallet = forms.ModelChoiceField(queryset=Wallet.objects.filter(name__startswith="运营资金"), label='付款账户')
	paid = forms.DecimalField(initial=0, max_digits=10, decimal_places=2, min_value=0.01, label="付款")

class TmorderRebateView(FormView):
	template_name = "base_form.html"
	form_class = TmorderRebateForm

	def form_valid(self, form):
		o = form.cleaned_data['organization']
		j = form.cleaned_data['tmorder']
		j, created = Tmorder.objects.get_or_create(oid=j, desc="天猫订单")
		self.task = j.task_ptr
		w = form.cleaned_data['wallet']
		p = form.cleaned_data['paid']
		cash = Money.objects.get(name="人民币")
		a = Account.get(o.root(), cash.item_ptr, "资产", w.name, None)
		b = Account.get_or_create(o, cash.item_ptr, "支出", "其他支出", None)
		Transaction.add(self.task, "返现", timezone.now(), a, -p, b)
		return super(TmorderRebateView, self).form_valid(form)

	def get_success_url(self):
		return reverse('task_detail_read', kwargs={'pk': self.task.id})

	def get_context_data(self, **kwargs):
		kwargs['title'] = "天猫订单返现"
		return super(TmorderRebateView, self).get_context_data(**kwargs)
