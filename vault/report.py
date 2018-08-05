# -*- coding: utf8 -*-
from django.utils import timezone
from .models import *
import os

def dump_profit():
	result = []
	balance = Decimal(0)
	e = begin_of_month()
	b = nth_previous_month(e, 1)
	while True:
		_e = next_month(b)
		if _e > e:
			break
		print "正在核算{}...".format(b)
		span = _e - b
		item = Money.objects.get(name='人民币')
		r = item_flow_report(item, span.days, _e)
		m_balance = Decimal(r[2]) * 1
		c_balance = Decimal(0)
		for commodity in Commodity.objects.exclude(supplier=Supplier.objects.get(name='耗材')):
			r = item_flow_report(commodity.item_ptr, span.days, _e)
			c_balance += Decimal(r[2]) * commodity.value
		balance += m_balance + c_balance
		result.append((b, m_balance, c_balance, m_balance+c_balance, balance))
		b = _e

	with open("/tmp/profit.csv", "wb") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(["核算期", "资金收支", "货物收发", "盈亏", "累计"])
		for r in result:
			writer.writerow(r)
	os.system("soffice /tmp/profit.csv")

def dump_stagnation():
	result = []
	e = begin_of_day()
	candidates = Split.objects.filter(account__name="出货").filter(transaction__time__gte=(e-timedelta(90))).filter(transaction__time__lt=e).values_list('account__item', flat=True).distinct()
	for c in Commodity.objects.exclude(supplier=Supplier.objects.get(name='耗材')).order_by('inproduction', 'supplier', 'name'):
		if c.id in candidates: continue
		c = Commodity.objects.get(pk=c)
		q = 0
		for s in ['完好', '残缺', '破损']:
			v = get_int_with_default(Account.objects.filter(item=c.item_ptr).filter(name=s).aggregate(Sum('balance'))['balance__sum'], 0)
			q += v
		if q != 0:
			result.append((c.inproduction, c, q, q*c.value))
			print "{}, {}, {}, {}".format(c.inproduction, c, float(q), float(q*c.value))

	with open("/tmp/stagnation.csv", "wb") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(["停产", "品名", "数量", "价值"])
		for r in result:
			writer.writerow(r)
	os.system("soffice /tmp/stagnation.csv")
