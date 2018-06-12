#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import django
from django.utils import timezone

#setup django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "launchpad.settings")
django.setup()

#add your codes here
import traceback
from vault.item import *
from vault.jdcommodity import *
from vault.jdorder import *
from vault.task import *
from vault.tmcommodity import *
from vault.tmorder import *
from django.utils import timezone
from django.utils import formats
from datetime import timedelta

def test():
	print (timezone.now())
	t = timezone.now().astimezone(timezone.get_current_timezone())
	print t
	t = t.replace(hour=0, minute=0, second=0, microsecond = 0)
	print t
	t = t - timedelta(1)
	print t

options = (
	["ic", "导入物资", Commodity.Import],
	["im", "导入货币", Money.Import],
	["ijdcm", "导入京东商品映射", Jdcommoditymap.Import],
	["ijdo", "导入京东订单", Jdorder.Import],
	["itmcm", "导入天猫商品映射", Tmcommoditymap.Import],
	["itml", "导入天猫订单列表", Tmorder.Import_List],
	["itmd", "导入天猫订单详情", Tmorder.Import_Detail],
	["t", "测试", test],
)

def command_handling():
	op = raw_input("请输入命令:")
	for key, desc, func in options:
		if key == op:
			func()
			return

	#invalid option, list commands
	for key, desc, func in options:
		print("{}: {}".format(key, desc))

try:
	while True:
		command_handling()
		print "----------------------------------------任务分割线----------------------------------------"
except (EOFError, KeyboardInterrupt) as e: #ctrl+d & ctrl+c
	print "再见!"
except Exception, e:
	traceback.print_exc()

print "End!"
