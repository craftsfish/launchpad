# -*- coding: utf8 -*-
from django.utils import timezone
from .models import *
import os

@transaction.atomic
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

@transaction.atomic
def dump_jd_profit():
	result = {}
	e = begin_of_month()
	b = nth_previous_month(e, 1)
	q = Transaction.objects.filter(desc__startswith='1.出货.').filter(time__gte=b).filter(time__lt=e).filter(task__desc='京东订单')
	for task_id in q.values_list('task', flat=True).distinct():
		task = Task.objects.get(id=task_id)

		#利润计算
		balance = 0
		for t in task.transactions.all():
			for s in t.splits.all():
				if s.account.category not in [2, 3]:
					continue
				if hasattr(s.account.item, 'commodity'):
					s.change_value = s.change * s.account.item.commodity.value * -s.account.sign()
				else:
					s.change_value = s.change * -s.account.sign()
				balance += s.change_value
		express_fee = get_decimal_with_default(Express.objects.filter(task=task_id).aggregate(Sum('fee'))['fee__sum'], 0)
		profit = balance - express_fee - 3 #包装人工预估每单3元

		#利润分配
		cost = 0
		candidates = []
		for i in task.transactions.filter(desc__contains=".出货."):
			splits = i.splits.order_by("account__category", "change")
			commodity = Commodity.objects.get(id=splits[1].account.item.id)
			if commodity.supplier == Supplier.objects.get(name='耗材'):
				continue
			quantity = splits[1].change
			cost += commodity.value * quantity
			candidates.append([commodity, quantity])
		if cost == 0:
			continue
		for c, q in candidates:
			if result.get(c.id) == None:
				result[c.id] = [c, 0]
			result[c.id][1] += profit / cost * c.value * q
		#print "任务: {} | 利润: {} | 成本: {}".format(task_id, profit, cost)
	with open("/tmp/profit.jd.csv", "wb") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(["品名", "利润"])
		def __key(v):
			c, vs = v
			return vs[1]
		for c, vs in sorted(result.items(), key=__key, reverse=True):
			writer.writerow(vs)
	os.system("soffice /tmp/profit.jd.csv")
