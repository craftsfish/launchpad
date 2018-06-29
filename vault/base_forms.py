# -*- coding: utf-8 -*-
from django import forms
from ground import *
from repository import Repository

class BaseCommodityStatusForm(forms.Form):
	status = forms.ChoiceField(choices=Itemstatus.choices[0:3])

class BaseRepositoryForm(forms.Form):
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None)

class BaseShipStatusForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices)

class BaseShipStatusReceiveForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices[0:1])

class BaseShipStatusSendForm(forms.Form):
	ship = forms.ChoiceField(choices=Shipstatus.choices[1:2])

class BaseKeywordForm(forms.Form):
	keyword = forms.CharField()
