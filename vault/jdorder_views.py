# -*- coding: utf-8 -*-
from .misc_views import *

class JdorderForm(forms.Form):
	jdorder = forms.IntegerField()
	organization = forms.ModelChoiceField(queryset=Organization.objects)

class JdorderMixin(FfsMixin):
	"""
	A mixin that provides a way to show and handle jdorder in a request.
	"""
	form_class = JdorderForm
	formset_class = CommodityDetailFormSet
	sub_form_class = CommodityShippingForm

	def formset_item_process(self, time, item, quantity, repository, status):
		pass

	def data_valid(self, form, formset):
		self.org = form.cleaned_data['organization']
		j = form.cleaned_data['jdorder']
		try:
			j = Jdorder.objects.get(oid=j)
		except Jdorder.DoesNotExist as e:
			j = Jdorder(oid=j, desc="京东订单")
			j.save()
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
			self.formset_item_process(t, c.item_ptr, q, r, s)
		return super(JdorderMixin, self).data_valid(form, formset)

class JdorderChangeView(JdorderMixin, TemplateView):
	template_name = "{}/jdorder_change.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status):
		if quantity > 0:
			Transaction.add_raw(self.task, "换货.收货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		else:
			Transaction.add_raw(self.task, "换货.发货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		return super(JdorderChangeView, self).formset_item_process(time, item, quantity, repository, status)

class JdorderCompensateView(JdorderMixin, TemplateView):
	template_name = "{}/jdorder_compensate.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status):
		Transaction.add_raw(self.task, "补发", time, self.org, item, ("资产", status, repository), -quantity, ("支出", "出货", repository))
		return super(JdorderCompensateView, self).formset_item_process(time, item, quantity, repository, status)

class JdorderReturnView(JdorderMixin, TemplateView):
	template_name = "{}/jdorder_return.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status):
		Transaction.add_raw(self.task, "退货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		return super(JdorderReturnView, self).formset_item_process(time, item, quantity, repository, status)
