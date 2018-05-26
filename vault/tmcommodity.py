# -*- coding: utf-8 -*-

from django.db import models
from item import *
from django.core.urlresolvers import reverse
from datetime import datetime
from django.utils import timezone

class Tmcommodity(models.Model):
	class Meta:
		ordering = ['id']

	id = models.CharField("商品编码", primary_key=True, max_length=60)
	name = models.CharField(max_length=120)

	def __str__(self):
		return "{}: {}".format(self.id, self.name)

class Tmcommoditymap(models.Model):
	class Meta:
		unique_together = ("tmcommodity", "since")
		ordering = ['tmcommodity', '-since']

	tmcommodity = models.ForeignKey(Tmcommodity)
	since = models.DateTimeField("生效时间")
	commodities = models.ManyToManyField(Commodity, verbose_name="商品")

	def str_time(self):
		return self.since.astimezone(timezone.get_current_timezone()).strftime("%Y-%m-%d %H:%M:%S")

	def str_commodities(self):
		result = ""
		for i, v in enumerate(self.commodities.all()):
			if i:
				result += ", "
			result += v.name
		return result

	def __str__(self):
		return self.str_time() + " | " + self.str_commodities()

	def get_absolute_url(self):
		return reverse('tmcommodity_detail', kwargs={'pk': self.tmcommodity.pk})

	@staticmethod
	def get(in_tmcommodity, in_timestamp):
		since = 0
		result = []
		m = Tmcommoditymap.objects.filter(tmcommodity=in_tmcommodity).filter(since__lte=in_timestamp).order_by("-since")
		if len(m):
			return m[0].commodities.all()
		else:
			return None

	@staticmethod
	def Import():
		with open('/tmp/tmcommoditymap.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			for l in reader:
				t = datetime.utcfromtimestamp(float(l[0])).replace(tzinfo=timezone.utc)
				try:
					tmc = Tmcommodity.objects.get(id=l[1])
				except Tmcommodity.DoesNotExist as e:
					tmc = Tmcommodity(id=l[1])
					tmc.save()
					print "增加天猫商品: {}".format(tmc)
				cs = l[2:]

				try:
					Tmcommoditymap.objects.filter(since=t).get(tmcommodity=tmc)
				except Tmcommoditymap.DoesNotExist as e:
					j = Tmcommoditymap(tmcommodity=tmc, since=t)
					j.save()
					for c in cs:
						try:
							i = Commodity.objects.get(name=c)
						except Commodity.DoesNotExist as e:
							i = Commodity(name=c, supplier=Supplier.objects.get(name="未知"))
							i.save()
							print "增加物资: {}".format(i)
						j.commodities.add(i)
					j.save()
					print "增加天猫商品映射: {}".format(j)
