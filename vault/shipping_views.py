# -*- coding: utf-8 -*-

from .models import *
from django import forms
from django.views.generic import FormView
from django.utils import timezone

class ShippingForm(forms.Form):
	o = Organization.objects.get(name="企业")
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

def purchase(task, time, organization, item, quantity, repository, status):
	cash = Item.objects.get(name="人民币")
	if repository:
		task.add_transaction("收货", time, organization, item, ("资产", "在库"), quantity, ("收入", "进货"))
	else:
		task.add_transaction("进货", time, organization, item, ("资产", "应收"), quantity, ("收入", "进货"))
	task.add_transaction("货款", time, organization, cash, ("负债", "应付货款"), quantity*item.value, ("支出", "进货"))
	if repository:
		task.add_transaction("入库", time, repository, item, ("资产", status), quantity, ("收入", "收货"))

def sale(task, time, organization, item, quantity, repository, status):
	cash = Item.objects.get(name="人民币")
	if repository:
		task.add_transaction("发货", time, organization, item, ("资产", "在库"), -quantity, ("支出", "出货"))
	else:
		task.add_transaction("出货", time, organization, item, ("负债", "应发"), quantity, ("支出", "出货"))
	task.add_transaction("营收", time, organization, cash, ("资产", "应收货款"), quantity*item.value, ("收入", "营收"))
	if repository:
		task.add_transaction("出库", time, repository, item, ("资产", status), -quantity, ("支出", "发货"))

def back_2_supplier(task, time, organization, item, quantity, repository, status):
	cash = Item.objects.get(name="人民币")
	if repository:
		task.add_transaction("发货", time, organization, item, ("资产", "在库"), -quantity, ("收入", "进货"))
	else:
		task.add_transaction("出货", time, organization, item, ("负债", "应发"), quantity, ("收入", "进货"))
	task.add_transaction("货款", time, organization, cash, ("资产", "应收货款"), quantity*item.value, ("支出", "进货"))
	if repository:
		task.add_transaction("出库", time, repository, item, ("资产", status), -quantity, ("收入", "收货"))

def callback(task, time, organization, item, quantity, repository, status):
	cash = Item.objects.get(name="人民币")
	if repository:
		task.add_transaction("收货", time, organization, item, ("资产", "在库"), quantity, ("支出", "出货"))
	else:
		task.add_transaction("进货", time, organization, item, ("资产", "应收"), quantity, ("支出", "出货"))
	task.add_transaction("货款", time, organization, cash, ("资产", "应收货款"), -quantity*item.value, ("收入", "营收"))
	if repository:
		task.add_transaction("入库", time, repository, item, ("资产", status), quantity, ("支出", "发货"))

class ShippingInCreateView(FormView):
	template_name = "{}/shipping_form.html".format(Organization._meta.app_label)
	form_class = ShippingForm
	TITLES = ("进货", "销售", "退供", "召回")
	handler = (
		purchase,
		sale,
		back_2_supplier,
		callback,
	)

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
				ShippingInCreateView.handler[self.shipping_type](self.task, timezone.now(), o, it, q, r, s)
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
			j.step = 3
		return context

	def get(self, request, *args, **kwargs):
		self.shipping_type = int(kwargs['type'])
		return super(ShippingInCreateView, self).get(request, *args, **kwargs)
