# -*- coding: utf8 -*-
import time
import enum
import csv
from datetime import datetime
from django.utils import timezone
from decimal import *

#csv
def csv_gb18030_2_utf8(f):
	for l in f:
		yield l.decode('gb18030').encode('utf8')

def csv_parser(csv_file, decoder, has_title, handler, *args):
	with open(csv_file, 'rb') as csvfile:
		if decoder:
			reader = csv.reader(decoder(csvfile))
		else:
			reader = csv.reader(csvfile)
		title = None
		if has_title:
			title = reader.next()
		for line in reader:
			handler(title, line, *args)

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

	@classmethod
	def s2v(cls, s):
		for i, v in cls.choices:
			if v == s:
				return i
		return None

class Itemstatus(BaseStatus):
	choices = tuple(enumerate(("应收", "完好", "残缺", "破损", "应发")))

class Shipstatus(BaseStatus):
	choices = tuple(enumerate(("收货", "发货")))

class ClearStatus(BaseStatus):
	choices = tuple(enumerate(("收款", "付款")))

@enum.unique
class DeliveryStatus(enum.IntEnum):
	inbook = 0
	delivered = 1
	cancel = 2

#express supplier mapping
express_supplier_map = (
	('中通', ('中通快递', '中通速递')),
	('邮政', ('EMS经济快递', '邮政EMS', '邮政快递包裹', '邮政EMS经济快递', 'EMS')),
	('顺丰', ('顺丰速运', '顺丰快递')),
	('百世', ('百世快递')),
	('韵达', ('韵达快递')),
	('京东', ('京东快递')),
	('申通', ('申通快递')),
	('天天', ('天天快递')),
	('圆通', ('圆通速递', '圆通快递')),
	('德邦', ('德邦物流')),
)
