# -*- coding: utf-8 -*-
from django import forms
from ground import *
from repository import Repository
from organization import Organization

class BaseOrganizationForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects, label="主体")

class BaseRootOrganizationForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects.filter(parent=None), label="主体")

class BaseIndividualForm(forms.Form):
	organization = forms.ModelChoiceField(queryset=Organization.objects.filter(name="个人"), label="主体")

class BaseCommodityStatusForm(forms.Form):
	status = forms.ChoiceField(choices=Itemstatus.choices[1:3], label="状态")

class BaseCommodityStatusHiddenForm(forms.Form):
	status = forms.ChoiceField(choices=Itemstatus.choices[1:3], widget=forms.HiddenInput)

class BaseRepositoryForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None, label="仓库")

class BaseRepositoryHiddenForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)

class BaseRepositoryChangeForm(forms.Form):
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_f = forms.ChoiceField(choices=Itemstatus.choices[1:3], widget=forms.RadioSelect, initial=0)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_t = forms.ChoiceField(choices=Itemstatus.choices[1:3], widget=forms.RadioSelect, initial=0)

class BaseRepositoryChangeHiddenForm(forms.Form):
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_f = forms.ChoiceField(choices=Itemstatus.choices[1:3], widget=forms.HiddenInput)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_t = forms.ChoiceField(choices=Itemstatus.choices[1:3], widget=forms.HiddenInput)

class BaseShipStatusForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices, label="收/发")

class BaseShipStatusReceiveForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices[0:1], label="收/发")

class BaseShipStatusSendForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices[1:2], label="收/发")

class BaseShipStatusHiddenForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices, widget=forms.HiddenInput)

class BaseKeywordForm(forms.Form):
	keyword = forms.CharField(label="关键字")

class BaseDescriptionForm(forms.Form):
	desc = forms.CharField(label="描述")

class BaseCommodityDetailForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	check = forms.BooleanField(required=False)
	quantity = forms.IntegerField()

class JdorderForm(forms.Form):
	jdorder = forms.IntegerField(label="订单编号")
	organization = forms.ModelChoiceField(queryset=Organization.objects.filter(name="为绿厨具专营店"), label="店铺")

	def clean(self):
		cleaned_data = super(JdorderForm, self).clean()
		order_id = cleaned_data.get("jdorder")
		if order_id > 100000000000:
			self.add_error('jdorder', "非法京东订单")

class TmorderForm(forms.Form):
	tmorder = forms.IntegerField(label="订单编号")
	organization = forms.ModelChoiceField(queryset=Organization.objects.filter(name="泰福高腾复专卖店"), label="店铺")

	def clean(self):
		cleaned_data = super(TmorderForm, self).clean()
		order_id = cleaned_data.get("tmorder")
		if order_id < 100000000000000000:
			self.add_error('tmorder', "非法天猫订单")
