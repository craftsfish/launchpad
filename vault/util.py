# -*- coding: utf-8 -*-

#shipping_out_future, 期货出货
#shippint_out, 期货发货
#shipping_out_actual, 现货出货
#shipping_deliver, 出库
#shipping_in_future, 期货进货
#shippint_in, 期货收货
#shipping_in_actual, 现货进货
#shipping_receive, 入库

def shipping_out_future(task, time, organization, item, quantity):
	task.add_transaction("期货出货", time, organization, item, ("负债", "应发"), quantity, ("支出", "出货"))

def shipping_out(task, time, organization, item, quantity):
	task.add_transaction("期货发货", time, organization, item, ("资产", "在库"), -quantity, ("负债", "应发"))

def shipping_deliver(task, time, item, quantity, repository):
	task.add_transaction("出库", time, repository, item, ("资产", "库存"), -quantity, ("支出", "出库"))
