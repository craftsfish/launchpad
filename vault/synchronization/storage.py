# -*- coding: utf8 -*-
import csv
from ..ground import *
from django.db import transaction
from ..models import *

@transaction.atomic
def import_storage(): #TO BE TESTED
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
	orgs = Organization.objects.filter(parent=None).exclude(name="个人")
	for k, v in merged.items():
		c, r, s, q = v
		Turbine.calibration_commodity(None, c, r, s, q, orgs)
