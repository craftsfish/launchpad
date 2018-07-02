# -*- coding: utf-8 -*-
from django import forms
from django.forms import formset_factory
from django.views.generic.base import ContextMixin
from misc_views import FfsMixin
from django.views.generic import TemplateView
from organization import *
from turbine import EmptyForm
from .models import *

class CalibrationMixin(ContextMixin):
	template_name = "vault/calibration.html"
	def get_context_data(self, **kwargs):
		context = super(CalibrationMixin, self).get_context_data(**kwargs)
		for form in context['formset']:
			cid = form['id'].value()
			s = form['status'].value()
			form.label_name = Commodity.objects.get(pk=cid).name
			form.label_status = Itemstatus.v2s(s)
			form.label_in_book = form['in_book'].value()
		return context

class StorageCalibarionForm(forms.Form):
	check = forms.BooleanField()

class CommodityStorageCalibarionForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	status = forms.ChoiceField(choices=Itemstatus.choices[1:4], widget=forms.HiddenInput)
	in_book = forms.IntegerField(widget=forms.HiddenInput)
	q1 = forms.IntegerField(min_value=0, max_value=9999, required=False)
	q2 = forms.IntegerField(min_value=0, max_value=9999, required=False)
	q3 = forms.IntegerField(min_value=0, max_value=9999, required=False)
	q4 = forms.IntegerField(min_value=0, max_value=9999, required=False)
CommodityStorageCalibarionFormSet = formset_factory(CommodityStorageCalibarionForm, extra=0)

class DailyCalibrationView(CalibrationMixin, FfsMixin, TemplateView):
	form_class = StorageCalibarionForm
	formset_class = CommodityStorageCalibarionFormSet
	sub_form_class = EmptyForm

	def get_formset_initial(self):
		d = []
		for c in ["T2005", "CB0066", "CB0060"]:
			c = Commodity.objects.get(name=c)
			r = Repository.objects.get(name="孤山仓")
			v = Account.objects.filter(item=c).filter(repository=r).filter(name="完好").aggregate(Sum('balance'))['balance__sum']
			if v: v = int(v)
			else: v = 0
			d.append({'id': c.id, 'status': 1, 'in_book': v})
		for c in Commodity.objects.order_by("calibration", "supplier", "name")[:10]:
			r = Repository.objects.get(name="孤山仓")
			v = Account.objects.filter(item=c).filter(repository=r).filter(name="完好").aggregate(Sum('balance'))['balance__sum']
			if v: v = int(v)
			else: v = 0
			d.append({'id': c.id, 'status': 1, 'in_book': v})
		return d

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
			return reverse('daily_calibration_match')

class DailyCalibrationMatchView(TemplateView):
	template_name = "{}/calibration_match.html".format(Organization._meta.app_label)

class ManualCalibrationCommodityForm(forms.Form):
	check = forms.BooleanField(required=False)
	id = forms.IntegerField(widget=forms.HiddenInput)
	quantity = forms.IntegerField()
	repository = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status = forms.ChoiceField(choices=Itemstatus.choices[1:4])
ManualCalibrationCommodityFormSet = formset_factory(ManualCalibrationCommodityForm, extra=0)

class ManualCalibrationCommodityFilterForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status = forms.ChoiceField(choices=Itemstatus.choices[1:4])
	keyword = forms.CharField()

class ManualCalibrationView(FfsMixin, TemplateView):
	template_name = "{}/manual_calibration.html".format(Organization._meta.app_label)
	form_class = EmptyForm
	formset_class = ManualCalibrationCommodityFormSet
	sub_form_class = ManualCalibrationCommodityFilterForm

	def data_valid(self, form, formset):
		self.task = None
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			c = Commodity.objects.get(pk=d['id'])
			q = d['quantity']
			s = Itemstatus.v2s(d['status'])
			r = Repository.objects.get(name=d['repository'])
			self.task = Turbine.calibration_commodity(self.task, c, r, s, q,
				Organization.objects.filter(parent=None).exclude(name="个人"))
		return super(ManualCalibrationView, self).data_valid(form, formset)

	def get_success_url(self):
		if self.task:
			return reverse('task_detail_read', kwargs={'pk': self.task.id})
		else:
			return reverse('daily_calibration_match')

class InferiorCalibrationView(CalibrationMixin, FfsMixin, TemplateView):
	form_class = StorageCalibarionForm
	formset_class = CommodityStorageCalibarionFormSet

	def get_formset_initial(self):
		d = []
		r = Repository.objects.get(name="孤山仓")
		for cid, status, quantity in Turbine.get_inferior(r):
			d.append({'id': cid, 'status': Itemstatus.s2v(status), 'in_book': quantity})
		return d
