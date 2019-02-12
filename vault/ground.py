# -*- coding: utf8 -*-
import time
import enum
import csv
import re
import os
import math
from datetime import datetime
from django.utils import timezone
from decimal import *

#csv
def csv_gb18030_2_utf8(f):
	for l in f:
		yield l.decode('gb18030').encode('utf8')

def csv_parser(csv_file, decoder, has_title, handler, *args):
	if not os.path.isfile(csv_file):
		print "csv文件{}不存在".format(csv_file)
		return
	print "正在导入{}...".format(csv_file)
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

def csv_line_2_str(line):
	result = ""
	for i in line:
		result += str(i) + ","
	return result

#misc
def get_column_value(table, row, column):
	for i, v in enumerate(table):
		if v == column:
			if row[i] and row[i][0] == '\t':
				return row[i][1:]
			else:
				return row[i]
	return None

def get_column_values(table, row, *columns):
	result = []
	for column in columns:
		result.append(get_column_value(table, row, column))
	return result

def get_int_with_default(data, default):
	try:
		return int(data)
	except:
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
	choices = tuple(enumerate(("应收", "完好", "破损", "应发")))

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
	('中通', ('中通快递', '中通速递', '中通')),
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

class NavItem(object):
	pass

class Container(object):
	pass

def now():
	return timezone.now().astimezone(timezone.get_current_timezone())

def now_as_seconds():
	return int(time.time())

def time_2_seconds(t):
	return time.mktime(t.timetuple())

def begin_of_day():
	return timezone.now().astimezone(timezone.get_current_timezone()).replace(hour=0, minute=0, second=0, microsecond = 0)

def begin_of_month():
	return timezone.now().astimezone(timezone.get_current_timezone()).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def nth_previous_month(d, n):
	if d.month > n:
		return d.replace(d.year, d.month-n)
	else:
		return d.replace(d.year-1, d.month+12-n)

def next_month(d):
	if d.month == 12:
		return d.replace(d.year+1, 1)
	else:
		return d.replace(d.year, d.month+1)

def is_tm_order(s):
	criteria = r'^\d{18,19}$'
	return re.compile(criteria).match(s)

def is_jd_order(s):
	criteria = r'^\d{11,11}$'
	return re.compile(criteria).match(s)

#def adt_now_utc()
#def adt_now_local()
#def adt_now_seconds()
#def adt_seconds_2_utc()
#def adt_seconds_2_local()
#def adt_utc_2_seconds()
#def adt_local_2_seconds()

def zt_jj_fee(province, weight):
	__map = (
		#李王中通快递价格表（9月1日）,,,,
		#区域,3㎏以内,,3㎏以上,
		#,首重,续重,首重,续重
		('江苏',3.5,0.5,3.7,0.7),
		('安徽',3.5,0.5,3.7,0.7),
		('上海',3.5,0.5,3.7,0.7),
		('浙江',3.5,0.5,3.7,0.7),
		('北京',6,3,6,3),
		('山东',4.5,1.5,6,3),
		('江西',4.5,1.5,6,3),
		('福建',4.5,1.5,6,3),
		('湖北',4.5,1.5,6,3),
		('湖南',4.5,1.5,6,3),
		('河南',4.5,1.5,6,3),
		('河北',4.5,1.5,6,3),
		('天津',4.5,1.5,6,3),
		('广东',4.5,1.5,6,3),
		('山西',5,2,6,5),
		('陕西',5,2,6,5),
		('吉林',5,2,6,5),
		('黑龙江',5,2,6,5),
		('四川',5,2,6,5),
		('广西',5,2,6,5),
		('辽宁',5,2,6,5),
		('重庆',5,2,6,5),
		('海南',8,5,8,6),
		('贵州',5,2,8,6),
		('甘肃',8,6,8,6),
		('云南',8,6,8,6),
		('内蒙古',8,6,8,6),
		('青海',8,6,8,6),
		('宁夏',8,6,8,6),
		('新疆',18,18,18,18),
		('西藏',18,18,18,18),
	)
	for p, b1, a1, b2, a2 in __map:
		if province.find(p) == 0:
			if weight <= 1.1:
				weight = 1
			weight = math.ceil(weight)
			if weight > 3:
				return b2 + (weight - 1) * a2
			else:
				return b1 + (weight - 1) * a1
	print "[Error]无法识别省份信息: {}".format(province)
	return 0

def zt_nj_fee(province, weight):
	weight = math.ceil(weight)
	if weight <= 1:
		return 3.5
	else:
		return 4.5

def express_fee_calculator_bs_nj(supplier, province, weight):
#区域	1公斤以内	1-2公斤	2-3公斤	首重1KG	续重
	__map = (
		('江苏',3.0,3.5,4,4.0,0.5),
		('浙江',3.0,3.5,4,4.0,0.5),
		('上海',3.0,3.5,4,4.0,0.5),
		('安徽',3.0,3.5,4,4.0,0.5),
		('北京',3.5,4,4,5.5,2.2),
		('广东',3.5,4,4,5.5,2.2),
		('山东',3.5,4,4,5.5,2.2),
		('福建',3.5,4,4,5.5,2.2),
		('天津',3.5,4,4,5.5,2.2),
		('河北',3.5,4,4,5.5,2.2),
		('江西',3.5,4,4,6,2.5),
		('河南',3.5,4,4,6,2.5),
		('湖北',3.5,4,4,6,2.5),
		('湖南',3.5,4,4,6,2.5),
		('山西',3.5,4,4,7,3.5),
		('陕西',3.5,4,4,7,3.5),
		('广西',3.5,4,4,7.5,4),
		('重庆',3.5,4,4,8,4.5),
		('辽宁',3.5,4,4,8.5,5),
		('吉林',3.5,4,4,8.5,5),
		('黑龙江',3.5,4,4,8.5,5.2),
		('四川',3.5,4,4,8.5,5.2),
		('云南',3.5,4,4,8,4.5),
		('甘肃',3.5,4,4,8,4.5),
		('贵州',3.5,4,4,8,4.5),
		('内蒙古',3.5,4,4,10,7),
		('宁夏',3.5,4,4,13,10),
		('青海',3.5,4,4,12,9),
		('海南',12,21,30,12,9),
		('新疆',18,33,48,18,15),
		('西藏',23,43,63,23,20),
	)
	if supplier != '百世':
		print "[Error]快递服务商 {} 不是百世".format(supplier)
		return 0
	for p, b1, b2, b3, b4, a4 in __map:
		if province.find(p) == 0:
			weight = math.ceil(weight)
			if weight > 3:
				return b4 + (weight - 1) * a4
			elif weight > 2:
				return b3
			elif weight > 1:
				return b2
			else:
				return b1
	print "[Error]无法识别省份信息: {}".format(province)
	return 0
