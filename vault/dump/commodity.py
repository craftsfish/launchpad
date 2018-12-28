# -*- coding: utf8 -*-
import csv
from ..ground import *
from django.db import transaction
from ..models import *

@transaction.atomic
def dump_commodity():
	with open("/tmp/commodity.csv", "wb") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(["编号", "供应商", "品名", "简称"])
		for i in Commodity.objects.exclude(supplier=Supplier.objects.get(name='耗材')).order_by('supplier', 'name'):
			writer.writerow([i.id, i.supplier, i.name])
