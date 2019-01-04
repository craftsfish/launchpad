# -*- coding: utf-8 -*-
from .models import *
from django.db.models import Q
from django.views.generic import ListView
from django.views.generic import RedirectView
from .security import *

def task_shipout(task):
	result = {}
	for t in task.transactions.all():
		for s in t.splits.all():
			if s.account.category not in [2, 3]:
				continue
			if hasattr(s.account.item, 'commodity'):
				cid = s.account.item.id
				if result.get(cid) == None:
					result[cid] = 0
				result[cid] += s.change * s.account.sign()
	return result

class CustomerListView(SecurityLoginRequiredMixin, ListView):
	model = Customer
	paginate_by = 1

	def get_queryset(self):
		k = self.kwargs['key']
		if k == '0':
			return Customer.objects.filter(contact__jdorder__desc='京东订单').order_by('recruit', 'counterfeit', 'join')
		elif k == '1':
			return Customer.objects.filter(contact__jdorder__desc='京东订单').order_by('recruit', '-counterfeit', 'join')
		else:
			return Customer.objects.filter(Q(contact__phone__contains=k) | Q(contact__jdorder__oid=get_int_with_default(k, 0)) | Q(contact__tmorder__oid=get_int_with_default(k,0))).order_by("counterfeit", 'recruit', 'join')

	def get_context_data(self, **kwargs):
		context = super(CustomerListView, self).get_context_data(**kwargs)
		for t in context['object_list']:
			t.flag = "买家"
			t.recruit_url = reverse('customer_recruit', kwargs={'uuid': t.uuid ,'key': 0})
			if t.counterfeit:
				t.recruit_url = reverse('customer_recruit', kwargs={'uuid': t.uuid, 'key': 1})
				t.flag = "刷手"
			t.join = utc_2_datetime(t.join).astimezone(timezone.get_current_timezone())
			t.recruited = True
			if t.recruit == 0:
				t.recruited = False
			t.recruit = utc_2_datetime(t.recruit).astimezone(timezone.get_current_timezone())
			t.contacts = t.contact_set.all()
			t.jdorders = Jdorder.objects.filter(contact__in=t.contact_set.all()).all()
			t.tmorders = Tmorder.objects.filter(contact__in=t.contact_set.all()).all()
			def __key(o):
				return o.time
			t.orders = sorted(list(t.jdorders) + list(t.tmorders), key=__key)
			total_shipouts = {}
			for o in t.orders:
				o.shipouts = []
				for cid, v in task_shipout(o).items():
					if total_shipouts.get(cid) == None:
						total_shipouts[cid] = 0
					total_shipouts[cid] += v
					c = Commodity.objects.get(id=cid)
					c.n = int(v)
					o.shipouts.append(c)
				s_addr = ''
				a = o.address
				while a:
					if a.level == 2:
						t.province = a.name
					s_addr = a.name + s_addr
					a = a.parent
				o.addr = s_addr
			remark = t.contacts[0].phone + ',' + t.province + ',' + t.flag + ',' + t.name
			max_value = 0
			greeting_commodity = None
			greeting_commodity_n = 0
			for cid, v in total_shipouts.items():
				c = Commodity.objects.get(id=cid)
				if c.value >= 3.0:
					remark += ',' + c.name + ':' + str(int(v))
				if c.value * v > max_value:
					max_value = c.value * v
					greeting_commodity = c
					greeting_commodity_n = v
			t.remark = remark
			if greeting_commodity:
				cname = greeting_commodity.abbrev
				if not cname:
					cname = greeting_commodity.name
				t.greeting = '[京东为绿厨具专营店]您在我家买过{}。加入老客户群，大额隐藏优惠券。做任务，领红包'.format(cname)
			else:
				t.greeting = '想请您做个天猫任务，送红包或者礼物，还有老客户优惠。'
		return context

class CustomerRecruitView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		return reverse('customer_list', kwargs={'key': kwargs['key']})

	def get(self, request, *args, **kwargs):
		i = kwargs['uuid']
		c = Customer.objects.get(uuid=i)
		c.recruit = now_as_seconds()
		c.save()
		return super(CustomerRecruitView, self).get(request, *args, **kwargs)
