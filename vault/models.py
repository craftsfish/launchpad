# -*- coding: utf-8 -*-
from django.db import models

class Platform(models.Model): #taobao, tmall, jd and etc.
	name = models.CharField(max_length=30, unique=True)

	def __str__(self):
		return self.name

from repository import *
from organization import *
from supplier import *
from item import *
from jdcommodity import *
from task import *
from jdorder import *
from account import *
from tmcommodity import *
from tmorder import *
from counterfeit import *
from wallet import *
from express import *

class Tmclear(models.Model):
	pid = models.CharField(max_length=30, primary_key=True, verbose_name="支付宝流水号")
	transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
	def __str__(self):
		return self.pid
