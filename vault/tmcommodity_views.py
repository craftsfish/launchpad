# -*- coding: utf-8 -*-
from .models import *
from django import forms
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic import CreateView
from django.views.generic import DetailView

class TmcommodityListView(ListView):
	model = Tmcommodity
	paginate_by = 64

	def get_context_data(self, **kwargs):
		context = super(TmcommodityListView, self).get_context_data(**kwargs)
		for c in context['object_list']:
			maps = Tmcommoditymap.objects.filter(tmcommodity=c).order_by("-since")
			if len(maps):
				c.map = maps[0]
			c.url = "https://item.tm.com/{}.html".format(c.id)
		return context

class TmcommodityDetailView(DetailView):
	model = Tmcommodity

	def get_context_data(self, **kwargs):
		context = super(TmcommodityDetailView, self).get_context_data(**kwargs)
		context['maps'] = self.object.tmcommoditymap_set.all()
		for m in context['maps']:
			m.t = m.str_time()
			m.d = m.str_commodities()
		return context

class TmcommoditymapForm(forms.ModelForm):
	class Meta:
		model = Tmcommoditymap
		fields = ['tmcommodity', 'since', 'commodities']
		widgets = {
			'since': forms.TextInput(attrs={"class": "form-control datetimepicker-input", "data-target": "#datetimepicker1", "data-toggle": "datetimepicker"}),
			'tmcommodity': forms.HiddenInput(),
		}

class TmcommoditymapCreateView(CreateView):
	model = Tmcommoditymap
	form_class = TmcommoditymapForm
	template_name_suffix = '_create_form'

	def get_initial(self):
		initial = super(TmcommoditymapCreateView, self).get_initial()
		initial['tmcommodity'] = Tmcommodity.objects.get(pk=self.kwargs['pk']).id
		initial['since'] = timezone.now()
		return initial
