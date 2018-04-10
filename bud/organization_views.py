# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import *
from django import forms
from django.http import HttpResponse
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import UpdateView

class OrganizationListView(ListView):
	model = Organization

class OrganizationDetailView(DetailView):
	model = Organization

class ParentOrganizationForm(forms.Form):
	parent = forms.ModelChoiceField(Organization.objects, required=False, label="隶属于")

class OrganizationUpdateView(UpdateView):
	model = Organization
	fields = ['name']
	template_name_suffix = '_update_form'

	def get_context_data(self, **kwargs):
		context = super(OrganizationUpdateView, self).get_context_data(**kwargs)
		parent = self.object.parent()
		if parent:
			context['parent'] = ParentOrganizationForm({"parent": parent.id})
		else:
			context['parent'] = ParentOrganizationForm()
		return context

	def post(self, request, *args, **kwargs):
		parent_id = request.POST["parent"]
		parent = None
		if parent_id != "":
			parent = Organization.objects.all().get(id=parent_id)
		org = self.get_object()
		if parent in org.descendants.all():
			return HttpResponse("({})隶属于当前组织，不能设定为上级!!!".format(parent))
		else:
			org.set_parent(parent)
			return super(OrganizationUpdateView, self).post(request, *args, **kwargs)
