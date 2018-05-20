# -*- coding: utf-8 -*-

def task_future_deliver(task, repository):
	for t in task.transactions.filter(desc="期货出货"):
		s = t.splits.get(account__category=1) #负债, 应发
		Shipping.future_deliver(task, t.time, s.account.organization, s.account.item, s.change, repository, "完好")

class Shipping:
	@staticmethod
	def future_out(task, time, organization, item, quantity):
		task.add_transaction("期货出货", time, organization, item, ("负债", "应发"), quantity, ("支出", "出货"))

	@staticmethod
	def future_deliver(task, time, organization, item, quantity, repository, status):
		task.add_transaction("期货发货", time, organization, item, ("资产", "在库"), -quantity, ("负债", "应发"))
		task.add_transaction("出库", time, repository, item, ("资产", status), -quantity, ("支出", "出库"))
