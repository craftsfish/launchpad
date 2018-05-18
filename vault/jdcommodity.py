# -*- coding: utf-8 -*-

from django.db import models
from item import *
from django.core.urlresolvers import reverse
from datetime import datetime
from django.utils import timezone

class Jdcommodity(models.Model):
	class Meta:
		ordering = ['id']

	id = models.BigIntegerField("商品编码", primary_key=True)
	name = models.CharField(max_length=120)

	def __str__(self):
		return "{}: {}".format(self.id, self.name)

class Jdcommoditymap(models.Model):
	class Meta:
		unique_together = ("jdcommodity", "since")
		ordering = ['jdcommodity', '-since']

	jdcommodity = models.ForeignKey(Jdcommodity, related_name="maps")
	since = models.DateTimeField("生效时间")
	items = models.ManyToManyField(Item, verbose_name="物品")

	def str_time(self):
		return self.since.astimezone(timezone.get_current_timezone()).strftime("%Y-%m-%d %H:%M:%S")

	def str_items(self):
		result = ""
		for i, v in enumerate(self.items.all()):
			if i:
				result += ", "
			result += v.name
		return result

	def __str__(self):
		return self.str_time() + " | " + self.str_items()

	def get_absolute_url(self):
		return reverse('jdcommodity_detail', kwargs={'pk': self.jdcommodity.pk})

	@staticmethod
	def get(in_jdcommodity, in_timestamp):
		since = 0
		result = []
		m = Jdcommoditymap.objects.filter(jdcommodity=in_jdcommodity).filter(since__lte=in_timestamp).order_by("-since")
		if len(m):
			return m[0].items.all()
		else:
			return None

	@staticmethod
	def Import():
		with open('/tmp/jdcommoditymap.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			for l in reader:
				t = datetime.utcfromtimestamp(float(l[0])).replace(tzinfo=timezone.utc)
				try:
					jdc = Jdcommodity.objects.get(id=int(l[1]))
				except Jdcommodity.DoesNotExist as e:
					jdc = Jdcommodity(id=int(l[1]))
					jdc.save()
					print "增加京东商品: {}".format(jdc)
				cs = l[2:]

				try:
					Jdcommoditymap.objects.filter(since=t).get(jdcommodity=jdc)
				except Jdcommoditymap.DoesNotExist as e:
					j = Jdcommoditymap(jdcommodity=jdc, since=t)
					j.save()
					for c in cs:
						try:
							i = Item.objects.get(name=c)
						except Item.DoesNotExist as e:
							i = Item(name=c, supplier=Supplier.objects.get(name="未知"))
							i.save()
							print "增加物资: {}".format(i)
						j.items.add(i)
					j.save()
					print "增加京东商品映射: {}".format(j)
