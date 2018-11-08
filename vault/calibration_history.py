# -*- coding: utf-8 -*-
from django.db import models
from item import *
from repository import *

class CalibrationHistory(models.Model):
	commodity = models.ForeignKey(Commodity)
	repository = models.ForeignKey(Repository)
	status = models.CharField(max_length=10)
	quantity = models.IntegerField()
	utc = models.IntegerField()
