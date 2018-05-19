# -*- coding: utf-8 -*-

from .models import *
from django import forms
from django.views.generic import FormView
from django.utils import timezone

class ShippingForm(forms.Form):
	o = Organization.objects.get(name="组织")
	os = []
	for i in o.descendants():
		os.append(i.id)
	r = Organization.objects.get(name="仓库")
	rs = []
	for i in r.descendants():
		rs.append(i.id)
	organization = forms.ModelChoiceField(queryset=Organization.objects.filter(id__in=os))
	repository = forms.ModelChoiceField(queryset=Organization.objects.filter(id__in=rs), required=False)
	ITEM_STATUS_CHOICES = (
		(0, "完好"),
		(1, "残缺"),
		(2, "破损"),
	)
	status = forms.ChoiceField(choices=ITEM_STATUS_CHOICES)

	@staticmethod
	def status_2_str(s):
		for i, v in ShippingForm.ITEM_STATUS_CHOICES:
			if i == s:
				return v
		return None

def get_sign(i):
	if i < 0:
		return "-"
	return "+"

def purchase(task, time, organization, item, quantity, repository, status):
	cash = Item.objects.get(name="人民币")
	account = ("资产", "应收")
	if repository:
		account = ("资产", "在库")
	task.add_transaction("进货("+get_sign(quantity)+")", time, organization, item, account, quantity, ("收入", "进货"))
	task.add_transaction("货款("+get_sign(quantity)+")", time, organization, cash, ("负债", "应付货款"), quantity*item.value, ("支出", "进货"))
	if repository:
		task.add_transaction("收货("+get_sign(quantity)+")", time, repository, item, ("资产", status), quantity, ("收入", "收货"))

class ShippingInCreateView(FormView):
	template_name = "{}/shipping_form.html".format(Organization._meta.app_label)
	form_class = ShippingForm
	TITLES = ("进货", "出货", "收货", "发货")

	def post(self, request, *args, **kwargs):
		self.shipping_type = int(kwargs['type'])
		self.task = Task.objects.get(pk=kwargs['task_id'])
		p = self.request.POST
		o = Organization.objects.get(pk=p['organization'])
		r = p.get('repository')
		if r:
			r = Organization.objects.get(pk=r)
		s = ShippingForm.status_2_str(int(p.get('status')))
		for i in range(int(p['items_total'])):
			if p.get("invoice_{}_include".format(i)) == "on":
				it = Item.objects.get(pk=p["invoice_{}_item".format(i)])
				q = int(p["invoice_{}_quantity".format(i)])
				purchase(self.task, timezone.now(), o, it, q, r, s)
		return super(ShippingInCreateView, self).post(request, *args, **kwargs)

	def get_success_url(self):
		return self.task.get_absolute_url()

	def get_context_data(self, **kwargs):
		context = super(ShippingInCreateView, self).get_context_data(**kwargs)
		context['title'] = ShippingInCreateView.TITLES[self.shipping_type]
		context['items'] = Item.objects.all()
		for i, j in enumerate(context['items']):
			j.name_check = "invoice_{}_include".format(i)
			j.name_item = "invoice_{}_item".format(i)
			j.name_quantity = "invoice_{}_quantity".format(i)
		return context

	def get(self, request, *args, **kwargs):
		self.shipping_type = int(kwargs['type'])
		return super(ShippingInCreateView, self).get(request, *args, **kwargs)
