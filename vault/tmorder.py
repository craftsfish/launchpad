# -*- coding: utf-8 -*-
import csv
import re
from django.db import models
from task import *
from ground import *
from tmcommodity import *
from organization import *
from account import *
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

class Tmtransaction:
	pass

class Tminvoice:
	pass

class Tmorder(Task):
	oid = models.BigIntegerField("订单编号", unique=True)
	TM_ORDER_STATUS = (
		(0, "等待买家付款"),
		(1, "买家已付款，等待卖家发货"),
		(2, "卖家已发货，等待买家确认"),
		(3, "交易成功"),
		(4, "交易关闭"),
	)
	status = models.IntegerField("状态", choices=TM_ORDER_STATUS, null=True, blank=True)
	fake = models.IntegerField("刷单", default=0)
	time = models.DateTimeField(default=timezone.now)
	repository = models.ForeignKey(Repository, null=True, blank=True)
	sale = models.DecimalField(max_digits=20, decimal_places=2, default=0)

	@staticmethod
	def statuses():
		r = []
		for i, v in Tmorder.TM_ORDER_STATUS:
			r.append(v)
		return r

	@staticmethod
	def str2status(s):
		for i, v in Tmorder.TM_ORDER_STATUS:
			if v == s:
				return i
		return -1

	@staticmethod
	def Import_List():
		#增加一条刷单Transaction
		def __add_fake_transaction(task, organization, repository, time):
			c = Commodity.objects.get(name="洗衣粉")
			Transaction.add_raw(task, "0.出货.{}".format(c.name), time, organization, c.item_ptr,
				("资产", "完好", repository), -1, ("支出", "出货", repository))

		def __handle_list(order_id, time, status, sale, fake, organization, repository):
			try: #更新
				o = Tmorder.objects.get(oid=order_id)
				if status == "交易关闭":
					o.task_ptr.delete_transactions_contains_desc('.出货.')
					return
				if o.fake != fake:
					o.task_ptr.delete_transactions_contains_desc('.出货.')
					if fake:
						__add_fake_transaction(o.task_ptr, organization, repository, time)
				elif fake:
					t = o.task_ptr.transactions.get(desc__startswith='0.出货.')
					s = t.splits.exclude(account__category=Account.str2category("支出"))[0]
					original_repository = s.account.repository
					if original_repository.id != repository.id: #仓库发生变化
						t.change_repository(original_repository, repository)

				o.status = Tmorder.str2status(status)
				o.fake = fake
				o.repository = repository
				o.sale = sale
				o.save()
			except Tmorder.DoesNotExist as e: #新增
				o = Tmorder(desc="天猫订单", oid=order_id, status=Tmorder.str2status(status), fake=fake, time=time, repository=repository, sale=sale)
				o.save()
				if status == "交易关闭":
					return
				if fake:
					__add_fake_transaction(o.task_ptr, organization, repository, time)

			#更新退货的仓库信息
			for t in o.task_ptr.transactions.filter(desc="退货"):
				for s in t.splits.all():
					a = s.account
					if a.repository.id == repository.id:
						break
					s.account = Account.get(a.organization, a.item, a.get_category_display(), a.name, repository)
					s.save()

		with open('/tmp/tm.list.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			org = Organization.objects.get(name="泰福高腾复专卖店")
			for i in reader:
				with transaction.atomic():
					print transaction.get_connection().isolation_level #todo
					status = get_column_value(title, i, "订单状态")
					if status not in Tmorder.statuses():
						print "[天猫]未知订单状态: {}".format(status)
						continue
					order_id = int(re.compile(r"\d+").search(get_column_value(title, i, "订单编号")).group())
					when = utc_2_datetime(cst_2_utc(get_column_value(title, i, "订单创建时间"), "%Y-%m-%d %H:%M:%S"))
					sale = Decimal(get_column_value(title, i, "买家应付货款"))
					remark = get_column_value(title, i, "订单备注")
					f = 0
					if remark.find("朱") != -1:
						f = 1
					repo = Repository.objects.get(name="孤山仓")
					if re.compile("南京仓").search(remark):
						repo = Repository.objects.get(name="南京仓")

					__handle_list(order_id, when, status, sale, f, org, repo)

	@staticmethod
	def Import_Detail():
		def __handle_detail(info, organization):
			repository=info.order.repository
			for i, v in enumerate(info.invoices):
				#retrieve existing status
				s = "{}.出货.".format(i+1)
				if info.order.task_ptr.transactions.filter(desc__startswith=s).exists(): #update commodity transactions
					for t in info.order.task_ptr.transactions.filter(desc__startswith=s):
							if v.status == "交易关闭":
								t.delete()
								continue

							s = t.splits.exclude(account__category=Account.str2category("支出"))[0]
							original_repository = s.account.repository
							if s.account.category == Account.str2category("负债") and v.status in ["卖家已发货，等待买家确认", "交易成功"]:
								a = s.account
								s.account = Account.get(a.organization, a.item, "资产", "完好", a.repository)
								s.change = -s.change
								s.save()

							if original_repository.id != repository.id: #仓库发生变化
								t.change_repository(original_repository, repository)
				else: #add commodity transactions
					if v.status == "交易关闭":
						continue
					for c in Tmcommoditymap.get(Tmcommodity.objects.get(pk=v.id), info.order.time):
						if v.status in ["等待买家付款", "买家已付款，等待卖家发货"]:
							Transaction.add_raw(info.order.task_ptr, "{}.出货.{}.{}".format(i+1, v.id, c.name), info.order.time, organization, c.item_ptr,
								("负债", "应发", repository), v.number, ("支出", "出货", repository))
						else:
							Transaction.add_raw(info.order.task_ptr, "{}.出货.{}.{}".format(i+1, v.id, c.name), info.order.time, organization, c.item_ptr,
								("资产", "完好", repository), -v.number, ("支出", "出货", repository))

		#Import_Detail
		ts = []
		with open('/tmp/tm.detail.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			bad_orders = set()
			for i in reader:
				oid = int(re.compile(r"\d+").search(get_column_value(title, i, "订单编号")).group())
				o = Tmorder.objects.get(oid=oid)

				#status check
				status = get_column_value(title, i, "订单状态")
				if status not in Tmorder.statuses():
					print "[天猫订单]发现新的订单状态: {}".format(status)
					bad_orders.add(o.oid)

				#fast check
				if o.fake or o.status == Tmorder.str2status("交易关闭"):
					continue

				#add Tmcommodity
				cid = get_column_value(title, i, "商家编码")
				if cid == "null":
					print "订单{}没有设定商家编码".format(oid)
				try:
					tmc = Tmcommodity.objects.get(id=cid)
				except Tmcommodity.DoesNotExist as e:
					tmc = Tmcommodity(id=cid)
				tmc.name=get_column_value(title, i, "标题")
				tmc.save()

				#tmcommodity mapping validation
				if not Tmcommoditymap.get(tmc, o.time):
					print "{}) {}:{} 缺乏商品信息".format(o.time.astimezone(timezone.get_current_timezone()), tmc.id, tmc.name)
					bad_orders.add(o.oid)

				#ignore invalid order
				if o.oid in bad_orders:
					continue

				found = False
				for t in ts:
					if t.order.oid == o.oid:
						found = True
						break
				if not found:
					t = Tmtransaction()
					t.order = o
					t.invoices = []
					ts.append(t)

				invc = Tminvoice()
				invc.id = tmc.id
				invc.number = int(get_column_value(title, i, "购买数量"))
				invc.status = status
				t.invoices.append(invc)

				org = Organization.objects.get(name="泰福高腾复专卖店")
				for t in ts:
					if t.order.oid in bad_orders:
						continue
					t.invoices = sorted(t.invoices, key = lambda i: (i.id + str(i.number)))
				__handle_detail(t, org)
