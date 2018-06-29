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

class BaseKeywordForm(forms.Form):
	keyword = forms.CharField()
