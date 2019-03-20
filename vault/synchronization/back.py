# -*- coding: utf8 -*-
import csv
from ..ground import *
from django.db import transaction
from ..models import *

@transaction.atomic
def import_back():
	def __handler(title, line, *args):
		r = Repository.objects.get(name=get_column_value(title, line, "仓库"))
		s = get_column_value(title, line, "状态")
		c = Commodity.objects.get(name=get_column_value(title, line, "品名"))
		q = int(get_column_value(title, line, "库存"))
		k = '{}.{}.{}'.format(c, r, s)
		if merged.get(k) != None:
			print "{} merged: {} + {}".format(k, merged[k][3], q)
			merged[k][3] += q
		else:
			merged[k] = [c, r, s, q]

	merged = {}
	csv_parser('/tmp/storage.csv', None, True, __handler, merged)
	task = Task(desc="退货回厂家.2019.03.18") #update me
	task.save()
	t = timezone.now()
	o = Organization.objects.get(name='上海腾复日用品有限公司') #update me
	def __key(i):
		k, v = i
		c, r, s, q = v
		return c.name
	for k, v in sorted(merged.items(), key=__key):
		c, r, s, q = v
		Transaction.add_raw(task, "退货", t, o, c.item_ptr, ("资产", s, r), -q, ("收入", "进货", r))
		cash = Money.objects.get(name="人民币")
		if c.supplier:
			Transaction.add_raw(task, "货款", t, o, cash.item_ptr, ("资产", "{}占款".format(c.supplier), None), q*c.value, ("支出", "进货.{}".format(c.supplier), None))
		else:
			Transaction.add_raw(task, "货款", t, o, cash.item_ptr, ("资产", "其他供应商占款", None), q*c.value, ("支出", "进货", None))
