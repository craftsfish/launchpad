# -*- coding: utf8 -*-
import csv
from ..ground import *
from django.db import transaction
from ..models import *

@transaction.atomic
def import_region():
	def __handler(title, line, *args):
		p = args[0]
		i = line[0]
		if re.compile("area").search(i):
			a = i[i.find('>')+1:]
			a, created = Address.objects.get_or_create(name=a, parent=None)
			if created:
				print "增加地区: {}".format(a.name)
			a.save()
			p.area = a
		elif re.compile("province").search(i):
			a = i[i.find('>')+1:]
			a, created = Address.objects.get_or_create(name=a, parent=p.area)
			if created:
				print "增加省份: {}".format(a.name)
			a.save()
			p.province = a
		elif re.compile("city").search(i):
			a = i[i.find('>')+1:]
			a, created = Address.objects.get_or_create(name=a, parent=p.province)
			if created:
				print "增加城市: {}".format(a.name)
			a.save()
			p.city = a

	#main
	class Parameter():
		pass
	p = Parameter()
	csv_parser('/tmp/region', None, None, __handler, p)
