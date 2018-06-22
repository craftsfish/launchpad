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
