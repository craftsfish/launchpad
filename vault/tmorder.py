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
from order import *
from turbine import *

class Tmtransaction:
	pass

class Tminvoice:
	pass

class Tmorder(Order, Task):
	oid = models.BigIntegerField("订单编号", unique=True)
	TM_ORDER_STATUS = (
		(0, "等待买家付款"),
		(1, "买家已付款，等待卖家发货"),
		(2, "卖家已发货，等待买家确认"),
		(3, "交易成功"),
		(4, "交易关闭"),
	)
	status = models.IntegerField("状态", choices=TM_ORDER_STATUS, null=True, blank=True)
	fake = models.IntegerField("刷单", default=0) #TODO, remove me and using conterfeit instead

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

				if o.task_ptr.transactions.filter(desc__startswith="微信刷单").exists() and not o.task_ptr.transactions.filter(desc="微信刷单.结算").exists():
					t = o.task_ptr.transactions.filter(desc__startswith="微信刷单").first().time
					Turbine.wechat_fake_clear(organization, o.task_ptr, t, sale)

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
					if s.change < 0:
						if a.repository.id != repository.id:
							s.account = Account.get_or_create(a.organization, a.item, a.get_category_display(), a.name, repository)
							s.save()

		with open('/tmp/tm.list.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			org = Organization.objects.get(name="泰福高腾复专卖店")
			for i in reader:
				with transaction.atomic():
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
		@transaction.atomic
		def __handle_detail(info, organization):
			o = Tmorder.objects.get(oid=info.oid)
			if o.fake or o.status == Tmorder.str2status("交易关闭"):
				return
			info.invoices = sorted(info.invoices, key = lambda i: (i.id + str(i.number)))

			repository=o.repository
			original_repository = None
			for i, v in enumerate(info.invoices):
				#retrieve existing status
				s = "{}.出货.".format(i+1)
				if o.task_ptr.transactions.filter(desc__startswith=s).exists(): #update commodity transactions
					if v.status == "交易关闭":
						for t in o.task_ptr.transactions.filter(desc__startswith=s):
							t.delete()
					else:
						Order.invoice_shipment_update_status(o.task_ptr, i+1, v.status in ["卖家已发货，等待买家确认", "交易成功"])

						for t in o.task_ptr.transactions.filter(desc__startswith=s):
							s = t.splits.exclude(account__category=Account.str2category("支出"))[0]
							original_repository = s.account.repository
							break
				else: #add commodity transactions
					if v.status == "交易关闭":
						continue
					if v.status in ["等待买家付款", "买家已付款，等待卖家发货"]:
						delivered = False
					else:
						delivered = True
					commodities = Tmcommoditymap.get(Tmcommodity.objects.get(pk=v.id), o.time)
					Order.invoice_shipment_create(o.task_ptr, o.time, organization, repository, i+1, v.id, commodities, v.number, delivered)

			if original_repository and original_repository.id != repository.id: #仓库发生变化
				Order.delivery_repository_update(o.task_ptr, original_repository, repository)

		#merge seperate detail information into it's corresponding transaction
		def __handle_raw(ts, l):
			found = False
			oid = int(re.compile(r"\d+").search(get_column_value(title, l, "订单编号")).group())
			for t in ts:
				if t.oid == oid:
					found = True
					break
			if not found:
				t = Tmtransaction()
				t.oid = oid
				t.invoices = []
				ts.append(t)

			#append current invoice
			invc = Tminvoice()
			invc.id = get_column_value(title, i, "商家编码")
			invc.name =get_column_value(title, i, "标题")
			invc.number = int(get_column_value(title, i, "购买数量"))
			invc.status = get_column_value(title, l, "订单状态")
			t.invoices.append(invc)

		#Import_Detail
		ts = [] #parse csv and store transaction information in ts
		with open('/tmp/tm.detail.csv', 'rb') as csvfile:
			reader = csv.reader(csv_gb18030_2_utf8(csvfile))
			title = reader.next()
			for i in reader:
				__handle_raw(ts, i)

		org = Organization.objects.get(name="泰福高腾复专卖店")
		for t in ts:
			bad = False
			for i in t.invoices:
				if i.id == "null":
					print "订单{}没有设定商家编码".format(t.oid)
				if i.status not in Tmorder.statuses():
					print "[天猫订单]发现新的订单状态: {}".format(i.status)
					bad = True
					break

				with transaction.atomic():
					tmc, created = Tmcommodity.objects.get_or_create(id=i.id)
					tmc.name=i.name
					tmc.save()
					o = Tmorder.objects.get(oid=t.oid)
					if not Tmcommoditymap.get(tmc, o.time):
						print "{}) {}:{} 缺乏商品信息".format(o.time.astimezone(timezone.get_current_timezone()), tmc.id, tmc.name)
						bad = True
						break

			if not bad:
				__handle_detail(t, org)
