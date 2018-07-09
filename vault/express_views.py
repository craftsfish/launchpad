# -*- coding: utf-8 -*-
from .models import *
from .security import *
from django.views.generic import ListView
from django.views.generic import FormView

class ExpressListView(ListView):
	model = Express

	def get_template_names(self):
		return "vault/express_list.html"

	def get_queryset(self):
		return Express.objects.filter(eid=int(self.kwargs['id']))

class ExpressClearForm(forms.Form):
	supplier = forms.ModelChoiceField(queryset=ExpressSupplier.objects.all(),  label='快递服务商')
	id = forms.IntegerField(label='快递单号')
	wallet = forms.ModelChoiceField(queryset=Wallet.objects.filter(name__startswith="运营资金"), label='付款账户')
	change = forms.DecimalField(initial=0, max_digits=20, decimal_places=2, min_value=0.01, label="支付金额")

class ExpressClearView(FormView):
	template_name = "base_form.html"
	form_class = ExpressClearForm

	def form_valid(self, form):
		o = Organization.objects.get(name="南京为绿电子科技有限公司")
		s = form.cleaned_data['supplier']
		i = form.cleaned_data['id']
		w = form.cleaned_data['wallet']
		c = form.cleaned_data['change']
		e, created = Express.objects.get_or_create(supplier=s, eid=i)
		e.fee = c
		e.clear = True
		e.save()
		cash = Money.objects.get(name="人民币")
		a = Account.get(o, cash.item_ptr, "资产", w.name, None)
		b = Account.get_or_create(o, cash.item_ptr, "支出", "其他支出", None)
		Transaction.add(None, "{}.{}".format(s.name, i), timezone.now(), a, -c, b)
		self.wallet = w
		return super(ExpressClearView, self).form_valid(form)

	def get_success_url(self):
		return reverse('wallet_detail', kwargs={'pk': self.wallet.id})
