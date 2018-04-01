#!/usr/bin/env python
from bud.models import *

class Console:
	@staticmethod
	def run():
		print Supplier.objects.all()
