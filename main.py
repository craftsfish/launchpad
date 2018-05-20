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

def test():
	t = Task(desc="经营调整")
	t.save()
	t.add_transaction("测试",timezone.now(), Organization.objects.get(pk=1), Item.objects.get(pk=1), ("资产", "库存"), 1, ("收入", "收货"))

options = (
	["ii", "导入物资", Item.Import],
	["ijcm", "导入京东商品映射", Jdcommoditymap.Import],
	["ijdo", "导入京东订单", Jdorder.Import],
	["itcm", "导入天猫商品映射", Tmcommoditymap.Import],
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
