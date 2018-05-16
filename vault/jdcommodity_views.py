# -*- coding: utf-8 -*-

from .models import *
from django import forms
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic import CreateView
from django.views.generic import DetailView

class JdcommodityListView(ListView):
	model = Jdcommodity
	paginate_by = 64

	def get_context_data(self, **kwargs):
		context = super(JdcommodityListView, self).get_context_data(**kwargs)
		for c in context['object_list']:
			c.map = Jdcommoditymap.objects.filter(jdcommodity=c).order_by("-since")[0]
			c.url = "https://item.jd.com/{}.html".format(c.id)
		return context

class JdcommodityDetailView(DetailView):
	model = Jdcommodity

	def get_context_data(self, **kwargs):
		context = super(JdcommodityDetailView, self).get_context_data(**kwargs)
		context['maps'] = self.object.maps.all()
		for m in context['maps']:
			m.t = m.str_time()
			m.d = m.str_items()
		return context

class JdcommoditymapForm(forms.ModelForm):
	class Meta:
		model = Jdcommoditymap
		fields = ['jdcommodity', 'since', 'items']
		widgets = {
			'since': forms.TextInput(attrs={"class": "form-control datetimepicker-input", "data-target": "#datetimepicker1", "data-toggle": "datetimepicker"}),
			'jdcommodity': forms.HiddenInput(),
		}

class JdcommoditymapCreateView(CreateView):
	model = Jdcommoditymap
	form_class = JdcommoditymapForm
	template_name_suffix = '_create_form'

	def get_initial(self):
		initial = super(JdcommoditymapCreateView, self).get_initial()
		initial['jdcommodity'] = Jdcommodity.objects.get(pk=self.kwargs['pk']).id
		initial['since'] = timezone.now()
		return initial
