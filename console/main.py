#!/usr/bin/env python
# -*- coding: utf8 -*-
from bud.models import *
from commodity import *

class Console:
	@staticmethod
	def run():
		print Supplier.objects.all()
		Test()
