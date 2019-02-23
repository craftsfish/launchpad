# -*- coding: utf8 -*-
import csv
from ..ground import *
from django.db import transaction
from ..models import *

@transaction.atomic
def dump_express():
	def __handler(title, line, *args):
		mark_as_proxy = False
		result = args[0]
		eid = line[0]
		handled = False
		if Express.objects.filter(eid=eid).exists():
			e = Express.objects.get(eid=eid)
			if e.clear:
				if mark_as_proxy:
					if not e.proxy:
						result.append([e.supplier, e.eid, e.fee])
						e.proxy = True
						e.save()
				else:
					result.append([e.supplier, e.eid, e.fee])
				handled = True
		if not handled:
			print "未结算快递费: {}".format(eid)
	result = []
	csv_parser('/tmp/in.csv', None, False, __handler, result)

	with open("/tmp/out.csv", "wb") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(["供应商", "单号", "费用"])
		total = 0
		for l in result:
			writer.writerow(l)
			total += l[2]
		print total
