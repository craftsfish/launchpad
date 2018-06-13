# -*- coding: utf8 -*-
from django.utils import timezone
from datetime import timedelta
from .models import *

class Turbine:
	@staticmethod
	def replenish():
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for c in Split.objects.filter(account__name="出货").filter(transaction__time__gte=(e-timedelta(28))).filter(transaction__time__lt=e).values_list('account__item', flat=True).distinct():
			if Commodity.objects.filter(pk=c).exists():
				c = Commodity.objects.get(pk=c)
				print c
