# -*- coding: utf8 -*-
import csv
from ..ground import *
from django.db import transaction
from ..models import *

@transaction.atomic
def dump_storage():
	commodities = Commodity.objects.exclude(supplier=Supplier.objects.get(name="耗材")).order_by("supplier", "name")
	repositories = Repository.objects.all()

	title = ['品名']
	title_composed = False
	result = []
	for c in commodities:
		line = [c.name]
		for r in repositories:
			for i, s in Itemstatus.choices[1:3]:
				if not title_composed:
					title.append('{}.{}'.format(r.name, s))
				v = Account.objects.filter(item=c).filter(repository=r).filter(name=s).aggregate(Sum('balance'))['balance__sum']
				if v: v = int(v)
				else: v = 0
				line.append(v)
		result.append(line)
		title_composed = True

	with open("/tmp/storage.csv", "wb") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(title)
		for r in result:
			writer.writerow(r)
