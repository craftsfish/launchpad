# -*- coding: utf8 -*-
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django import forms
from .models import *

class EmptyForm(forms.Form):
	pass

class Turbine:
	@staticmethod
	def get_shipping_out_information(commodity, repository, span):
		r = []
		speed = 0
		active = 0
		decay = 0.7
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for i in range(span):
			q = Split.objects.filter(account__item=commodity).filter(account__repository=repository).filter(account__name="出货")
			q = q.filter(transaction__time__gte=(e-timedelta(1))).filter(transaction__time__lt=e)
			v = q.aggregate(Sum('change'))['change__sum']
			if v: v = int(v)
			else: v = 0
			r.append(v)
			speed += decay ** i * (1 - decay) * v
			if v: active += 1
			e -= timedelta(1)
		speed = speed * active / span
		r.append(speed)
		return r

	@staticmethod
	def get_replenish_information(commodity, repository, speed, threshold):
		inventory = Account.objects.filter(item=commodity).filter(repository=repository).filter(name__in=["完好", "应收"]).aggregate(Sum('balance'))['balance__sum']
		if inventory: inventory = int(inventory)
		else: inventory = 0
		if speed <= 0:
			return [8888, -inventory]
		else:
			return [inventory/speed, speed * threshold - inventory]

	@staticmethod
	def replenish():
		l = []
		e = timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)
		for c in Split.objects.filter(account__name="出货").filter(transaction__time__gte=(e-timedelta(28))).filter(transaction__time__lt=e).values_list('account__item', flat=True).distinct():
			if Commodity.objects.filter(pk=c).exists():
				c = Commodity.objects.get(pk=c)
				c.detail = []
				need_refill = False
				for r in Repository.objects.order_by("id"):
					shipping = Turbine.get_shipping_out_information(c, r, 10)
					speed = shipping[len(shipping)-1]
					level, refill = Turbine.get_replenish_information(c, r, speed, 30)
					if refill > 0:
						need_refill = True
					if refill != 0:
						c.detail.append([r, level, refill])
				if need_refill:
					l.append(c)
		for c in l:
			for repo, level, refill in c.detail:
				print "{}: {} | 库存天数: {} | 补仓数量: {}".format(c, repo, level, refill)
		return l
