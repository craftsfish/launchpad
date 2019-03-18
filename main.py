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
from vault.sync import *
from vault.report import *
from vault.synchronization.wkq import *
from vault.synchronization.region import *
from vault.dump.commodity import *
from vault.dump.express import *
from vault.dump.storage import *
from vault.synchronization.commodity import *

@transaction.atomic
def test():
	for a in Account.objects.filter(name="残缺"):
		b, created = Account.objects.get_or_create(organization=a.organization, item=a.item, category=a.category, repository=a.repository, name='破损')
		if created: print "[账户]增加<{}>账户: {}".format(b.item, b)
		for s in Split.objects.filter(account=a):
			s.account = b
			s.save()
	for a in Account.objects.filter(name="残缺").filter(balance=0):
		a.delete()

def __quit():
	raise EOFError()

options = (
	["aa", "增加账户", Turbine.add_account],
	["b", "构造系统使用环境", Turbine.build],
	["cr", "仓库盘点时间校准", calibration_reset],
	["cs", "仓库校准", Turbine.calibration_storage],
	["dc", "导出物资清单", dump_commodity],
	["de", "导出快递明细", dump_express],
	["dp", "导出利润报告", dump_profit],
	["dvf", "导出价值(现金+物资)流", dump_value_flow],
	["ds", "导出库存", dump_storage],
	["ic", "导入物资", import_commodity],
	["icme", "导入传美打印快递信息", Sync.import_cm_express],
	["ijdcm", "导入京东商品映射", Jdcommoditymap.Import],
	["ijde", "导入京东订单快递信息", Sync.import_jd_express],
	["ijdac", "导入京东推广结算信息", Sync.import_jd_advertise_clear],
	["ijdoc", "导入京东订单结算信息", Sync.import_jd_order_clear],
	["ijdwc", "导入京东钱包结算信息", Sync.import_jd_wallet_clear],
	["ijdf", "导入京东刷单信息", Jdorder.import_fake_order],
	["im", "导入货币", Money.Import],
	["ix", "导入其他", import_misc],
	["ir", "导入地域信息", import_region],
	["irqwy", "导入人气无忧刷单数据", import_rqwy],
	["itmc", "导入天猫结算信息", Sync.import_tm_clear],
	["itmcm", "导入天猫商品映射", Tmcommoditymap.Import],
	["itme", "导入天猫订单快递信息", Sync.import_tm_express],
	["iwkqd", "导入威客圈流水", import_wkq_detail],
	["iwkqob", "导入威客圈流量任务详情", import_wkq_order_browse],
	["iwkqos", "导入威客圈销量任务详情", import_wkq_order_sale],
	["iwkqr", "导入威客圈转账申请", import_wkq_request],
	["iwkqt", "导入威客圈转账信息", import_wkq_transfer],
	["ibse", "导入百世快递结算信息", Sync.import_bs_express],
	["iyde", "导入韵达快递结算信息", Sync.import_yd_express],
	["iyze", "导入邮政快递结算信息", Sync.import_yz_express],
	["izte", "导入中通快递结算信息", Sync.import_zt_express],
	["izbq", "导入zbq快递结算信息", import_zbq_express],
	["q", "退出系统", __quit],
	["r", "例行操作", import_order],
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
