# -*- coding: utf8 -*-
from django.utils import timezone
from .models import *

def dump_item_flow():
	balance = Decimal(0)
	e = timezone.now().astimezone(timezone.get_current_timezone()).replace(2018, 8, 1, 0, 0, 0, 0)
	b = timezone.now().astimezone(timezone.get_current_timezone()).replace(2018, 7, 1, 0, 0, 0, 0)
	span = e - b
	print span
	item = Money.objects.get(name='人民币')
	r = item_flow_report(item, span.days, e)
	balance += Decimal(r[2]) * 1
	for commodity in Commodity.objects.exclude(supplier=Supplier.objects.get(name='耗材')):
		r = item_flow_report(commodity.item_ptr, span.days, e)
		balance += Decimal(r[2]) * commodity.value
	print balance
