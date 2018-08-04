# -*- coding: utf8 -*-
from django.utils import timezone
from .models import *

def dump_item_flow():
	e = timezone.now().astimezone(timezone.get_current_timezone()).replace(2018, 8, 1, 0, 0, 0, 0)
	b = timezone.now().astimezone(timezone.get_current_timezone()).replace(2018, 7, 1, 0, 0, 0, 0)
	span = e - b
	print span
	item = Money.objects.get(name='人民币')
	print item_flow_report(item, span.days, e)
