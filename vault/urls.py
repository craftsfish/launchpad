from django.conf.urls import url
from supplier_views import *
from organization_views import *
from item_views import *
from commodity_views import *
from account_views import *
from transaction_views import *
from jdcommodity_views import *
from tmcommodity_views import *
from task_views import *
from misc_views import *
from jdorder_views import *
from tmorder_views import *
from chore_views import *
from wallet_views import *
from purchase_views import *
from calibration_views import *

urlpatterns = [
	#supplier
	url(r'^supplier/$', SupplierListView.as_view(), name='supplier_list'),

	#organization
	url(r'^organization/$', OrganizationListView.as_view(), name='organization_list'),

	#item
	url(r'^item/$', ItemListView.as_view(), name='item_list'),
	url(r'^item/(?P<pk>[\d]+)/organization/(?P<org>[\d]+)/$', BookDetailView.as_view(), name='book_detail'),

	#commodity
	url(r'^commodity/$', CommodityListView.as_view(), name='commodity_list'),
	url(r'^commodity/(?P<pk>[\d]+)/$', CommodityDetailView.as_view(), name='commodity_detail'),

	#account
	url(r'^account/$', AccountListView.as_view(), name='account_list'),
	url(r'^account/(?P<uuid>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/root/$', AccountDetailView.as_view(), name='account_detail'),
	url(r'^account/(?P<uuid>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/$', AccountDetailViewRead.as_view(), name='account_detail_read'),
	url(r'^account/fake/wechat/$', AccountDetailViewRead.as_view(), name='account_fake_wechat', kwargs={'pk': 87}),

	#wallet
	url(r'^wallet/$', WalletListView.as_view(), name='wallet_list'),
	url(r'^wallet/(?P<pk>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/$', WalletDetailView.as_view(), name='wallet_detail'),

	#transaction
	url(r'^transaction/$', TransactionListView.as_view(), name='transaction_list'),
	url(r'^transaction/(?P<pk>[\d]+)/$', TransactionDetailView.as_view(), name='transaction_detail'),
	url(r'^transaction/(?P<pk>[\d]+)/change/$', TransactionUpdateView.as_view(), name='transaction_update'),
	url(r'^transaction/(?P<pk>[\d]+)/duplicate/$', TransactionDuplicateView.as_view(), name='transaction_duplicate'),
	url(r'^transaction/(?P<pk>[\d]+)/delete/from/(?P<task_id>[\d]+)/$', TransactionDeleteView.as_view(), name='transaction_delete'),

	#jdcommodity
	url(r'^jdcommodity/$', JdcommodityListView.as_view(), name='jdcommodity_list'),
	url(r'^jdcommodity/(?P<pk>[\d]+)/$', JdcommodityDetailView.as_view(), name='jdcommodity_detail'),
	url(r'^jdcommodity/(?P<pk>[\d]+)/map/create/$', JdcommoditymapCreateView.as_view(), name='jdcommoditymap_create'),

	#tmcommodity
	url(r'^tmcommodity/$', TmcommodityListView.as_view(), name='tmcommodity_list'),
	url(r'^tmcommodity/(?P<pk>[\w]+)/$', TmcommodityDetailView.as_view(), name='tmcommodity_detail'),
	url(r'^tmcommodity/(?P<pk>[\w]+)/map/create/$', TmcommoditymapCreateView.as_view(), name='tmcommoditymap_create'),

	#task
	url(r'^task/$', TaskListView.as_view(), name='task_list'),
	url(r'^task/(?P<pk>[\d]+)/root/$', TaskDetailView.as_view(), name='task_detail'),
	url(r'^task/(?P<pk>[\d]+)/$', TaskDetailViewRead.as_view(), name='task_detail_read'),
	url(r'^task/(?P<pk>[\d]+)/delete/$', TaskDeleteView.as_view(), name='task_delete'),
	url(r'^task/(?P<pk>[\d]+)/clear/$', TaskClearView.as_view(), name='task_clear'),
	url(r'^task/(?P<pk>[\d]+)/settle/$', TaskSettleView.as_view(), name='task_settle'),
	url(r'^task/(?P<pk>[\d]+)/previous/$', TaskPreviousView.as_view(), name='task_previous'),
	url(r'^task/(?P<pk>[\d]+)/next/$', TaskNextView.as_view(), name='task_next'),
	url(r'^task/(?P<pk>[\d]+)/clear/bill/$', TaskClearBillView.as_view(), name='task_clear_bill'),
	url(r'^task/(?P<pk>[\d]+)/invoice/$', TaskInvoiceView.as_view(), name='task_invoice'),

	#tmorder
	url(r'^tmorder/change/$', TmorderChangeView.as_view(), name='tmorder_change'),
	url(r'^tmorder/compensate/$', TmorderCompensateView.as_view(), name='tmorder_compensate'),
	url(r'^tmorder/return/$', TmorderReturnView.as_view(), name='tmorder_return'),
	url(r'^tmorder/wechat/fake/$', TmorderWechatFakeView.as_view(), name='tmorder_wechat_fake'),
	url(r'^tmorder/(?P<pk>[\d]+)/$', TmorderDetailViewRead.as_view(), name='tmorder_detail_read'),
	url(r'^tmorder/rebate/$', TmorderRebateView.as_view(), name='tmorder_rebate'),

	#jdorder
	url(r'^jdorder/change/$', JdorderChangeView.as_view(), name='jdorder_change'),
	url(r'^jdorder/compensate/$', JdorderCompensateView.as_view(), name='jdorder_compensate'),
	url(r'^jdorder/return/$', JdorderReturnView.as_view(), name='jdorder_return'),
	url(r'^jdorder/wechat/fake/$', JdorderWechatFakeView.as_view(), name='jdorder_wechat_fake'),
	url(r'^jdorder/(?P<pk>[\d]+)/$', JdorderDetailViewRead.as_view(), name='jdorder_detail_read'),
	url(r'^jdorder/rebate/$', JdorderRebateView.as_view(), name='jdorder_rebate'),

	#misc
	url(r'^misc/daily_task/$', DailyTaskView.as_view(), name='daily_task'),
	url(r'^misc/retail/$', RetailView.as_view(), name='retail'),
	url(r'^misc/change/$', ChangeView.as_view(), name='change'),
	url(r'^misc/commodity/change/repository/$', ChangeRepositoryView.as_view(), name='change_repository'),
	url(r'^misc/receivable/commodity/$', ReceivableCommodityView.as_view(), name='receivable_commodity'),

	#purchase
	url(r'^misc/purchase/default/$', PurchaseView.as_view(), name='purchase'),
	url(r'^misc/purchase/tfg/$', TfgPurchaseView.as_view(), name='tfg_purchase'),
	url(r'^misc/purchase/yst/$', YstPurchaseView.as_view(), name='yst_purchase'),
	url(r'^misc/purchase/kml/$', KmlPurchaseView.as_view(), name='kml_purchase'),
	url(r'^misc/purchase/other/$', OtherPurchaseView.as_view(), name='other_purchase'),
	url(r'^misc/purchase/append/$', AppendPurchaseView.as_view(), name='append_purchase'),

	url(r'^misc/daily/calibration/$', DailyCalibrationView.as_view(), name='daily_calibration'),
	url(r'^misc/manual/calibration/$', ManualCalibrationView.as_view(), name='manual_calibration'),
	url(r'^misc/daily/calibration/match/$', DailyCalibrationMatchView.as_view(), name='daily_calibration_match'),
	url(r'^misc/pay/wechat/recruit/bonus/$', PayWechatRecruitBonusView.as_view(), name='pay_wechat_recruit_bonus'),
	url(r'^misc/operation/account/clear/$', OperationAccountClearView.as_view(), name='operation_account_clear'),
	url(r'^misc/help/$', HelpView.as_view(), name='help'),

	#chore
	url(r'^chore/$', ChoreListView.as_view(), name='chore_list'),
]
