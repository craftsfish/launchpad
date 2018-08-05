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
