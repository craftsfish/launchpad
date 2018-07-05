# -*- coding: utf-8 -*-
from misc_views import *

class ReturnToSupplierForm(BaseDescriptionForm, BaseRootOrganizationForm): pass
class ReturnToSupplierSubForm(BaseKeywordForm, BaseCommodityStatusForm, BaseRepositoryForm): pass
class ReturnToSupplierDetailForm(BaseCommodityStatusHiddenForm, CommodityDetailBaseForm): pass
ReturnToSupplierDetailFormSet = formset_factory(ReturnToSupplierDetailForm, extra=0)

class SupplierServiceMixin(FfsMixin):
	formset_class = ReturnToSupplierDetailFormSet
	sub_form_class = ReturnToSupplierSubForm

	def get_formset_initial(self):
		result = []
		repositories = Account.objects.filter(name__in=["残缺", "破损"]).exclude(balance=0).order_by('repository').values_list('repository', flat=True).distinct()
		for repo in repositories:
			r = {}
			for a in Account.objects.filter(name__in=["残缺", "破损"]).exclude(balance=0).filter(repository=repo):
				if r.get(a.item.id) == None:
					r[a.item.id] = [0, 0]
				if a.name == "残缺":
					r[a.item.id][0] += a.balance
				else:
					r[a.item.id][1] += a.balance
			def __key(x):
				c = Commodity.objects.get(id=x[0])
				if c.supplier:
					return c.supplier.name + c.name
				else:
					return "None" + c.name
			for cid, v in sorted(r.items(), key=__key):
				if v[0]:
					result.append({'id': cid, 'quantity': int(v[0]), 'repository': repo, 'check': False, 'status': Itemstatus.s2v("残缺")})
				if v[1]:
					result.append({'id': cid, 'quantity': int(v[1]), 'repository': repo, 'check': False, 'status': Itemstatus.s2v("破损")})
		return result

	def get_context_data(self, **kwargs):
		context = super(SupplierServiceMixin, self).get_context_data(**kwargs)
		for form in context['formset']:
			cid = form['id'].value()
			c = Commodity.objects.get(pk=cid)
			rid = form['repository'].value()
			r = Repository.objects.get(pk=rid)
			s = form['status'].value()
			form.label_repo = r.name
			form.label_commodity = c.name
			form.label_status = Itemstatus.v2s(s)
		return context

class ReturnToSupplierView(SupplierServiceMixin, TemplateView):
	template_name = "{}/return_to_supplier.html".format(Organization._meta.app_label)
	form_class = ReturnToSupplierForm

	def data_valid(self, form, formset):
		self.task = Task(desc="退货回厂家.{}".format(form.cleaned_data['desc']))
		self.task.save()
		t = timezone.now()
		o = form.cleaned_data['organization']
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			q = d['quantity']
			if not q: continue
			c = Commodity.objects.get(pk=d['id'])
			r = d['repository']
			s = Itemstatus.v2s(d['status'])
			Transaction.add_raw(self.task, "退货", t, o, c.item_ptr, ("资产", s, r), -q, ("收入", "进货", r))
			cash = Money.objects.get(name="人民币")
			if c.supplier:
				Transaction.add_raw(self.task, "货款", t, o, cash.item_ptr, ("资产", "{}占款".format(c.supplier), None), q*c.value, ("支出", "进货.{}".format(c.supplier), None))
			else:
				Transaction.add_raw(self.task, "货款", t, o, cash.item_ptr, ("资产", "其他供应商占款", None), q*c.value, ("支出", "进货", None))
		return super(ReturnToSupplierView, self).data_valid(form, formset)

class ChangeWithSupplierForm(BaseDescriptionForm, BaseRootOrganizationForm):
	repository = forms.ModelChoiceField(queryset=Repository.objects, empty_label=None, label="收货仓库")
class ChangeWithSupplierView(SupplierServiceMixin, TemplateView):
	template_name = "vault/change_with_supplier.html"
	form_class = ChangeWithSupplierForm

	def data_valid(self, form, formset):
		self.task = Task(desc="回厂家换货.{}".format(form.cleaned_data['desc']))
		self.task.save()
		t = timezone.now()
		o = form.cleaned_data['organization']
		repo = form.cleaned_data['repository']
		for f in formset:
			d = f.cleaned_data
			if not d['check']: continue
			q = d['quantity']
			if not q: continue
			c = Commodity.objects.get(pk=d['id'])
			r = d['repository']
			s = Itemstatus.v2s(d['status'])
			Transaction.add_raw(self.task, "换货", t, o, c.item_ptr, ("资产", "应收", repo), q, ("资产", s, r))
		return super(ChangeWithSupplierView, self).data_valid(form, formset)
