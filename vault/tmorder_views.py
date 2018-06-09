# -*- coding: utf-8 -*-
from .misc_views import *

class TmorderForm(forms.Form):
	tmorder = forms.IntegerField()
	organization = forms.ModelChoiceField(queryset=Organization.objects)

class TmorderMixin(FfsMixin):
	"""
	A mixin that provides a way to show and handle tmorder in a request.
	"""
	form_class = TmorderForm
	formset_class = CommodityDetailFormSet
	sub_form_class = CommodityShippingForm

	def formset_item_process(self, time, item, quantity, repository, status):
		pass

	def data_valid(self, form, formset):
		self.org = form.cleaned_data['organization']
		o = form.cleaned_data['tmorder']
		try:
			o = Tmorder.objects.get(oid=o)
		except Tmorder.DoesNotExist as e:
			o = Tmorder(oid=o, desc="天猫订单")
			o.save()
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
			self.formset_item_process(t, c.item_ptr, q, r, s)
		return super(TmorderMixin, self).data_valid(form, formset)

class TmorderChangeView(TmorderMixin, TemplateView):
	template_name = "{}/tmorder_change.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status):
		if quantity > 0:
			Transaction.add(self.task, "换货.收货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		else:
			Transaction.add(self.task, "换货.发货", time, self.org, item, ("资产", status, repository), quantity, ("支出", "出货", repository))
		return super(TmorderChangeView, self).formset_item_process(time, item, quantity, repository, status)

class TmorderCompensateView(TmorderMixin, TemplateView):
	template_name = "{}/tmorder_compensate.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status):
		Transaction.add(self.task, "补发", time, self.org, item, ("资产", status, repository), -quantity, ("支出", "出货", repository))
		return super(TmorderCompensateView, self).formset_item_process(time, item, quantity, repository, status)

class TmorderReturnView(TmorderMixin, TemplateView):
	template_name = "{}/tmorder_return.html".format(Organization._meta.app_label)

	def formset_item_process(self, time, item, quantity, repository, status):
		#when order information is synchronized, we will adjust the repository of deliver, now just use what user chose
		Transaction.add(self.task, "退货", time, self.org, item, ("资产", status, repository), quantity, ("资产", "完好", repository))
		return super(TmorderReturnView, self).formset_item_process(time, item, quantity, repository, status)
