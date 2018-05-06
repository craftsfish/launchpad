#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import django

#setup django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "launchpad.settings")
django.setup()

#add your codes here
import traceback
from vault.item import *
from vault.jd_commodity import *
from vault.jd_order import *

options = (
	["ii", "导入物资", Item.Import],
	["ijcm", "导入京东商品映射", Jdcommoditymap.Import],
	["ijdo", "导入京东订单", Jdorder.Import],
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
