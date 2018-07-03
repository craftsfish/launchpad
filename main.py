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
from vault.turbine import *
from vault.order import *
from django.utils import timezone
from django.utils import formats
from datetime import timedelta
from vault.jdorder import *

def test():
	for n in Split.objects.filter(transaction__desc="刷单.发货").values_list('account__item__name', flat=True).distinct():
		print n
	pass

def __quit():
	raise EOFError()

options = (
	["aa", "增加账户", Turbine.add_account],
	["b", "构造系统使用环境", Turbine.build],
	["cs", "仓库校准", Turbine.calibration_storage],
	["ds", "导出库存", Turbine.dump_storage],
	["ic", "导入物资", Commodity.Import],
	["ijdcm", "导入京东商品映射", Jdcommoditymap.Import],
	["ijdo", "导入京东订单", Jdorder.Import],
	["ijdf", "导入京东刷单信息", Jdorder.import_fake_order],
	["im", "导入货币", Money.Import],
	["itmcm", "导入天猫商品映射", Tmcommoditymap.Import],
	["itml", "导入天猫订单列表", Tmorder.Import_List],
	["itmd", "导入天猫订单详情", Tmorder.Import_Detail],
	["q", "退出系统", __quit],
	["t", "测试", test],
	["ucw", "更新盘库有效截至日期", Turbine.update_calibration_window],
	["uocl", "更新废弃商品清单", Turbine.update_obsolete_commodity_list],
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

print "The End!"
