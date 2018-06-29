# -*- coding: utf-8 -*-
from django import forms
from ground import *
from repository import Repository

class BaseCommodityStatusForm(forms.Form):
	status = forms.ChoiceField(choices=Itemstatus.choices[0:3])

class BaseCommodityStatusHiddenForm(forms.Form):
	status = forms.ChoiceField(choices=Itemstatus.choices[0:3], widget=forms.HiddenInput)

class BaseRepositoryForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)

class BaseRepositoryHiddenForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)

class BaseRepositoryChangeForm(forms.Form):
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_f = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.RadioSelect, initial=0)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)
	status_t = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.RadioSelect, initial=0)

class BaseRepositoryChangeHiddenForm(forms.Form):
	repository_f = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_f = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)
	repository_t = forms.ModelChoiceField(queryset=Repository.objects, widget=forms.HiddenInput)
	status_t = forms.ChoiceField(choices=Itemstatus.choices, widget=forms.HiddenInput)

class BaseShipStatusForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices)

class BaseShipStatusReceiveForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices[0:1])

class BaseShipStatusSendForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices[1:2])

class BaseShipStatusHiddenForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices, widget=forms.HiddenInput)

class BaseKeywordForm(forms.Form):
	keyword = forms.CharField()

class BaseCommodityDetailForm(forms.Form):
	id = forms.IntegerField(widget=forms.HiddenInput)
	check = forms.BooleanField(required=False)
	quantity = forms.IntegerField()
