# -*- coding: utf-8 -*-

from django.db import models
from item import *
from datetime import datetime
from django.utils import timezone

class Jdcommoditymap(models.Model):
	class Meta:
		unique_together = ("jdcommodity", "since")

	jdcommodity = models.BigIntegerField("京东商品编码")
	since = models.DateTimeField("生效时间")
	items = models.ManyToManyField(Item, verbose_name="物品")

	def __str__(self):
		result = str(self.since) + ", " + str(self.jdcommodity)
		for i in self.items.all():
			result += ", " + i.name
		return result

	@staticmethod
	def Import():
		with open('/tmp/jdcommodity.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			for l in reader:
				t = datetime.utcfromtimestamp(float(l[0])).replace(tzinfo=timezone.utc)
				jid = l[1]
				cs = l[2:]

				try:
					Jdcommoditymap.objects.filter(since=t).get(jdcommodity=jid)
				except Jdcommoditymap.DoesNotExist as e:
					j = Jdcommoditymap(jdcommodity=jid, since=t)
					j.save()
					for c in cs:
						j.items.add(Item.objects.get(name=c))
					j.save()
					print "增加京东商品映射: {}".format(j)
