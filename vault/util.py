# -*- coding: utf-8 -*-

#shipping_out_future, 期货出货
#shippint_out, 期货发货
#shipping_out_actual, 现货出货
#repository_deliver, 出库
#shipping_in_future, 期货进货
#shippint_in, 期货收货
#shipping_in_actual, 现货进货
#shipping_receive, 入库

def shipping_out_future(task, time, organization, item, quantity):
	task.add_transaction("期货出货", time, organization, item, ("负债", "应发"), quantity, ("支出", "出货"))

def shipping_out(task, time, organization, item, quantity):
	task.add_transaction("期货发货", time, organization, item, ("资产", "在库"), -quantity, ("负债", "应发"))

def repository_deliver(task, time, repository, item, quantity, status):
	task.add_transaction("出库", time, repository, item, ("资产", status), -quantity, ("支出", "出库"))

def task_future_deliver(task, repository):
	for t in task.transactions.filter(desc="期货出货"):
		s = t.splits.get(account__category=1) #负债, 应发
		shipping_out(task, t.time, s.account.organization, s.account.item, s.change)
		repository_deliver(task, t.time, repository, s.account.item, s.change, "完好")
