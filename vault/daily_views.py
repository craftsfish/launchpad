# -*- coding: utf-8 -*-
from .misc_views import *

class TransShipmentInForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects)

class TransShipmentInView(FfsMixin, TemplateView):
	template_name = "{}/trans_shipment_in.html".format(Organization._meta.app_label)
	form_class = TransShipmentInForm
	formset_class = CommodityDetailBaseFormSet
	sub_form_class = CommodityShippingBaseForm

	def data_valid(self, form, formset):
		self.task = Task(desc="串入")
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
			Transaction.add(self.task, "串入", t, o, c.item_ptr, ("资产", "应收", r), q, ("收入", "串货", r))
			cash = Money.objects.get(name="人民币")
			Transaction.add(self.task, "货款", t, o, cash.item_ptr, ("负债", "应付货款", None), q*c.value, ("支出", "进货", None))
		return super(TransShipmentInView, self).data_valid(form, formset)
