# -*- coding: utf8 -*-
import csv
from ..ground import *
from django.db import transaction
from ..models import *

@transaction.atomic
def import_commodity():
	def __handler(title, line, *args):
		cid, abbrev = get_column_values(title, line, '编号', '简称')
		c = Commodity.objects.get(id=cid)
		c.abbrev = abbrev
		c.save()

	#main
	csv_parser('/tmp/commodity.csv', None, True, __handler)
