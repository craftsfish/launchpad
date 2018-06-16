# -*- coding: utf-8 -*-
from django.db import models
from item import *
from django.core.urlresolvers import reverse
from datetime import datetime
from django.utils import timezone
from django.db import transaction

class Jdcommodity(models.Model):
	class Meta:
		ordering = ['id']

	id = models.BigIntegerField("商品编码", primary_key=True)
	name = models.CharField(max_length=120)

	def __str__(self):
		return "{} : {}".format(self.id, self.name)

class Jdcommoditymap(models.Model):
	class Meta:
		unique_together = ("jdcommodity", "since")
		ordering = ['jdcommodity', '-since']

	jdcommodity = models.ForeignKey(Jdcommodity, related_name="maps")
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
		return reverse('jdcommodity_detail', kwargs={'pk': self.jdcommodity.pk})

	@staticmethod
	def get(in_jdcommodity, in_timestamp):
		since = 0
		result = []
		m = Jdcommoditymap.objects.filter(jdcommodity=in_jdcommodity).filter(since__lte=in_timestamp).order_by("-since")
		if len(m):
			return m[0].commodities.all()
		else:
			return None

	@staticmethod
	def Import():
		@transaction.atomic
		def __csv_handler(l):
			t = datetime.utcfromtimestamp(float(l[0])).replace(tzinfo=timezone.utc)
			jdc, created = Jdcommodity.objects.get_or_create(id=int(l[1]))
			if created:
				print "增加京东商品: {}".format(jdc)
			cs = l[2:]

			try:
				Jdcommoditymap.objects.filter(since=t).get(jdcommodity=jdc)
			except Jdcommoditymap.DoesNotExist as e:
				j = Jdcommoditymap(jdcommodity=jdc, since=t)
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
				print "增加京东商品映射: {}".format(j)

		with open('/tmp/jdcommoditymap.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			for l in reader:
				__csv_handler(l)
