# -*- coding: utf-8 -*-
from .misc_views import *
from django.utils import timezone

class PurchaseForm(BaseDescriptionForm, BaseRepositoryForm, BaseRootOrganizationForm): pass

class PurchaseCommodityForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	check = forms.BooleanField(required=False)
	desc = forms.CharField(required=False, widget=forms.HiddenInput)
PurchaseCommodityFormSet = formset_factory(PurchaseCommodityForm, extra=0)

class PurchaseMixin(FfsMixin):
	template_name = "{}/purchase.html".format(Organization._meta.app_label)
	form_class = PurchaseForm
	formset_class = PurchaseCommodityFormSet
	sub_form_class = BaseKeywordForm
	trans_shipment = False

	def get_task(self, form):
		if self.trans_shipment:
			self.task = Task(desc="串货.{}".format(form.cleaned_data['desc']))
		else:
			self.task = Task(desc="进货.{}".format(form.cleaned_data['desc']))
		self.task.save()

	def data_valid(self, form, formset):
		self.get_task(form)
		if not self.task:
			return self.render_to_response(self.get_context_data(form=form, formset=formset))
		t = timezone.now().replace(microsecond=0)
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
			name = "进货"
			if not self.trans_shipment and c.supplier:
				name += "." + c.supplier.name
			Transaction.add_raw(self.task, "货款", t, o, cash.item_ptr, ("负债", "应付货款", None), q*c.value, ("支出", name, None))
		return super(PurchaseMixin, self).data_valid(form, formset)

class SmartPurchaseMixin(PurchaseMixin):
	def get_formset_initial(self):
		r = []
		for c in Turbine.replenish(self.get_supplier()):
			for repo, inventory, speed, level, refill in c.detail:
				r.append({'id': c.id, 'quantity': int(refill), 'check': False, 'desc': "{}, 库存:{}, 速度:{}, 可售天数{}".format(repo, inventory, speed, level)})
		return r

	def get_context_data(self, **kwargs):
		context = super(SmartPurchaseMixin, self).get_context_data(**kwargs)
		for form in context['formset']:
			cid = form['id'].value()
			c = Commodity.objects.get(pk=cid)
			form.label = c.name
			form.note = form['desc'].value()
		return context

class TfgPurchaseView(SmartPurchaseMixin, TemplateView):
	def get_supplier(self):
		return Supplier.objects.get(name="泰福高")

class YstPurchaseView(SmartPurchaseMixin, TemplateView):
	def get_supplier(self):
		return Supplier.objects.get(name="原森太")

class KmlPurchaseView(SmartPurchaseMixin, TemplateView):
	def get_supplier(self):
		return Supplier.objects.get(name="凯曼隆")

class OtherPurchaseView(SmartPurchaseMixin, TemplateView):
	def get_supplier(self):
		return None

class PurchaseView(PurchaseMixin, TemplateView):
	pass

class TransShipmentView(PurchaseMixin, TemplateView):
	trans_shipment = True

class AppendPurchaseForm(BaseRepositoryForm, BaseRootOrganizationForm):
	task = forms.IntegerField()

class AppendPurchaseView(PurchaseMixin, TemplateView):
	template_name = "{}/purchase.html".format(Organization._meta.app_label)
	form_class = AppendPurchaseForm

	def get_task(self, form):
		try:
			self.task = Task.objects.get(pk=form.cleaned_data['task'])
		except Task.DoesNotExist as e:
			self.task = None
			self.error = "任务不存在!"
