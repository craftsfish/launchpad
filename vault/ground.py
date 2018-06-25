# -*- coding: utf8 -*-
import time
import enum
from datetime import datetime
from django.utils import timezone
from decimal import *

#csv
def csv_gb18030_2_utf8(f):
	for l in f:
		yield l.decode('gb18030').encode('utf8')

#misc
def get_column_value(table, row, column):
	for i, v in enumerate(table):
		if v == column:
			return row[i]
	return None

def get_column_values(table, row, *columns):
	result = []
	for column in columns:
		result.append(get_column_value(table, row, column))
	return result

def get_int_with_default(data, default):
	if data != None:
		return int(data)
	return default

def get_decimal_with_default(data, default):
	if data != None:
		return Decimal(data)
	return default

def cst_2_utc(str_time, str_format):
	# UTC = LOCAL + LOCAL.TZ
	# UTC = LOCALA + LOCALA.TZ = LOCALA + LOCALB.TZ - (LOCALB.TZ - LOCALA.TZ)
	return time.mktime(time.strptime(str_time, str_format)) - (time.timezone - (-28800))

def utc_2_datetime(utc):
	return datetime.utcfromtimestamp(utc).replace(tzinfo=timezone.utc)

class BaseStatus:
	@classmethod
	def v2s(cls, c):
		for i, v in cls.choices:
			if i == int(c):
				return v
		return None

class Itemstatus(BaseStatus):
	choices = tuple(enumerate(("完好", "残缺", "破损")))

class Shipstatus(BaseStatus):
	choices = tuple(enumerate(("收货", "发货")))

@enum.unique
class DeliveryStatus(enum.IntEnum):
	inbook = 0
	delivered = 1
	cancel = 2
