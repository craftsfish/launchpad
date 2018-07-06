# -*- coding: utf8 -*-
import csv

class Sync(object):
	@staticmethod
	def rqwy():
		with open('/tmp/rqwy.finished.csv', 'rb') as csvfile:
			reader = csv.reader((csvfile))
			title = reader.next()
			for l in reader:
				print l
