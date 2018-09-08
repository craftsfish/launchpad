# -*- coding: utf8 -*-
from django.utils import timezone
from .models import *
import os

@transaction.atomic
def dump_value_flow():
	result = []
	balance = Decimal(0)
	e = begin_of_month()
	b = nth_previous_month(e, 2)
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

@transaction.atomic
def __dump_profit(desc, abbrev):
	total = 0
	result = {}
	e = begin_of_month()
	e = nth_previous_month(e, 1)
	b = nth_previous_month(e, 1)
	q = Transaction.objects.filter(desc__startswith='1.出货.').filter(time__gte=b).filter(time__lt=e).filter(task__desc=desc)
	for task_id in set(q.values_list('task', flat=True)):
		task = Task.objects.get(id=task_id)
		splits, balance, express_fee, contribution = task_profit(task)
		for k, v in contribution.items():
			c = Commodity.objects.get(id=k)
			if result.get(c.id) == None:
				result[c.id] = [c, 0]
			result[c.id][1] += v[2]
			total += v[2]
			#if k == 78: #2005
				#print "{},{}".format(task_id, v[2])
	csv_file_path = "/tmp/profit.{}.csv".format(abbrev)
	print "[{}]{}: {} | 详情: {}".format(desc, b, total, csv_file_path)
	with open(csv_file_path, "wb") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(["品名", "利润"])
		def __key(v):
			c, vs = v
			return vs[1]
		for c, vs in sorted(result.items(), key=__key, reverse=True):
			writer.writerow(vs)
	#os.system("soffice /tmp/profit.jd.csv")

def dump_profit():
	for desc, abbrev in (('京东订单', 'jd'), ('天猫订单', 'tm')):
		__dump_profit(desc, abbrev)
