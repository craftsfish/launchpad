# -*- coding: utf-8 -*-
from .misc_views import *
from django.utils import timezone
from django.views.generic import RedirectView
from .turbine import *
from .base_forms import *

class JdorderDetailViewRead(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		try:
			return reverse('task_detail_read', kwargs={'pk': Jdorder.objects.get(oid=kwargs['pk']).id})
		except Jdorder.DoesNotExist as e:
			return reverse('chore_list')

class JdorderMixin(FfsMixin):
	"""
	A mixin that provides a way to show and handle jdorder in a request.
	"""
	form_class = JdorderForm
	formset_class = CommodityDetailFormSet
	sub_form_class = CommodityShippingForm

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		pass

	def data_valid(self, form, formset):
		self.org = form.cleaned_data['organization']
		j = form.cleaned_data['jdorder']
		j, created = Jdorder.objects.get_or_create(oid=j, desc="京东订单")
		self.task = j.task_ptr
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
		return super(JdorderMixin, self).data_valid(form, formset)

class JdorderChangeView(JdorderMixin, TemplateView):
	template_name = "{}/jdorder_change.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		if ship == "收货":
			Transaction.add_raw(self.task, "换货.收货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		else:
			Transaction.add_raw(self.task, "换货.发货", time, self.org, item, ("资产", status, repository), -quantity, ("支出", "出货", repository))
		return super(JdorderChangeView, self).formset_item_process(time, item, quantity, repository, status, ship)

class JdorderCompensateView(JdorderMixin, TemplateView):
	template_name = "{}/jdorder_compensate.html".format(Organization._meta.app_label)
	sub_form_class = CommoditySendForm

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		Transaction.add_raw(self.task, "补发", time, self.org, item, ("资产", status, repository), -quantity, ("支出", "出货", repository))
		return super(JdorderCompensateView, self).formset_item_process(time, item, quantity, repository, status, ship)

class JdorderReturnView(JdorderMixin, TemplateView):
	template_name = "{}/jdorder_return.html".format(Organization._meta.app_label)
	sub_form_class = CommodityReceiveForm

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		Transaction.add_raw(self.task, "退货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		return super(JdorderReturnView, self).formset_item_process(time, item, quantity, repository, status, ship)

class JdorderWechatFakeView(FakeOrderCandidatesMixin, JdorderMixin, TemplateView):
	template_name = "{}/jdorder_wechat_fake.html".format(Organization._meta.app_label)
	sub_form_class = CommoditySendForm

	def formset_item_process(self, time, item, quantity, repository, status, ship):
		o = self.task.jdorder
		o.counterfeit = Counterfeit.objects.get(name="微信")
		o.save()
		Transaction.add_raw(self.task, "刷单.发货", time, self.org, item, ("资产", status, repository), -quantity, ("支出", "出货", repository))
		return super(JdorderWechatFakeView, self).formset_item_process(time, item, quantity, repository, status, ship)

class JdorderRebateForm(JdorderForm):
	wallet = forms.ModelChoiceField(queryset=Wallet.objects.filter(name__startswith="运营资金"), label='付款账户')
	paid = forms.DecimalField(initial=0, max_digits=10, decimal_places=2, min_value=0.01, label="付款")

class JdorderRebateView(FormView):
	template_name = "base_form.html"
	form_class = JdorderRebateForm

	def form_valid(self, form):
		o = form.cleaned_data['organization']
		j = form.cleaned_data['jdorder']
		j, created = Jdorder.objects.get_or_create(oid=j, desc="京东订单")
		self.task = j.task_ptr
		w = form.cleaned_data['wallet']
		p = form.cleaned_data['paid']
		cash = Money.objects.get(name="人民币")
		a = Account.get(o.root(), cash.item_ptr, "资产", w.name, None)
		b = Account.get_or_create(o, cash.item_ptr, "支出", "其他支出", None)
		Transaction.add(self.task, "返现", timezone.now(), a, -p, b)
		return super(JdorderRebateView, self).form_valid(form)

	def get_success_url(self):
		return reverse('task_detail_read', kwargs={'pk': self.task.id})

	def get_context_data(self, **kwargs):
		kwargs['title'] = "京东订单返现"
		return super(JdorderRebateView, self).get_context_data(**kwargs)
