from django.conf.urls import url
from supplier_views import *
from item_views import *
from book_views import *
from commodity_views import *
from account_views import *
from transaction_views import *
from jdcommodity_views import *
from tmcommodity_views import *
from task_views import *
from misc_views import *
from jdorder_views import *
from tmorder_views import *
from wallet_views import *
from purchase_views import *
from calibration_views import *
from repository_views import *
from supplier_service_views import *
from express_views import *
from calibration_history_views import *
from compound_commodity_views import *
from customer_views import *
from address_views import *

urlpatterns = [
	#expose to outsider
	url(r'^$', HelpView.as_view(), name='help'),

	#supplier
	url(r'^supplier/$', SupplierListView.as_view(), name='supplier_list'),

	#item
	url(r'^item/$', ItemListView.as_view(), name='item_list'),
	url(r'^item/(?P<pk>[\d]+)/organization/(?P<org>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/$', BookDetailView.as_view(), name='book_detail'),
	url(r'^repository/(?P<repo>[\d]+)/(?P<commodity>[\d]+)/(?P<status>[\d]+)/$', RepositoryDetailView.as_view(), name='repository_detail'),

	#commodity
	url(r'^commodity/$', CommodityListView.as_view(), name='commodity_list'),
	url(r'^commodity/stagnation/$', CommodityStagnationListView.as_view(), name='commodity_stagnation_list'),
	url(r'^commodity/(?P<pk>[\d]+)/$', CommodityDetailView.as_view(), name='commodity_detail'),

	#compound commodity
	url(r'^compoundcommodity/$', CompoundCommodityListView.as_view(), name='compound_commodity_list'),
	url(r'^compoundcommodity/(?P<pk>[\d]+)/$', CompoundCommodityDetailView.as_view(), name='compound_commodity_detail'),

	#address
	url(r'^address/(?P<key>.*)/$', AddressListView.as_view(), name='address_list'),

	#customer
	url(r'^customer/(?P<key>[-\w\d]+)/$', CustomerListView.as_view(), name='customer_list'),
	url(r'^customer/(?P<uuid>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/recruit/(?P<key>[\d]+)/$', CustomerRecruitView.as_view(), name='customer_recruit'),

	#account
	url(r'^account/$', AccountListView.as_view(), name='account_list'),
	url(r'^account/(?P<uuid>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/root/$', AccountDetailView.as_view(), name='account_detail'),
	url(r'^account/(?P<uuid>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/$', AccountDetailViewRead.as_view(), name='account_detail_read'),
	url(r'^account/fake/wechat/$', AccountDetailViewRead.as_view(), name='account_fake_wechat', kwargs={'pk': 87}),
	url(r'^account/(?P<uuid>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/delete/$', AccountDeleteView.as_view(), name='account_delete'),
	url(r'^account/(?P<uuid>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/report/$', AccountReportView.as_view(), name='account_report'),

	#wallet
	url(r'^wallet/(?P<pk>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/$', WalletDetailView.as_view(), name='wallet_detail'),

	#transaction
	url(r'^transaction/$', TransactionListView.as_view(), name='transaction_list'),
	url(r'^transaction/(?P<pk>[\d]+)/$', TransactionDetailView.as_view(), name='transaction_detail'),
	url(r'^transaction/(?P<pk>[\d]+)/change/$', TransactionUpdateView.as_view(), name='transaction_update'),
	url(r'^transaction/(?P<pk>[\d]+)/duplicate/$', TransactionDuplicateView.as_view(), name='transaction_duplicate'),
	url(r'^transaction/(?P<pk>[\d]+)/delete/$', TransactionDeleteView.as_view(), name='transaction_delete'),
	url(r'^transaction/(?P<pk>[\d]+)/revert/$', TransactionRevertView.as_view(), name='transaction_revert'),

	#jdcommodity
	url(r'^jdcommodity/$', JdcommodityListView.as_view(), name='jdcommodity_list'),
	url(r'^jdcommodity/(?P<pk>[\d]+)/$', JdcommodityDetailView.as_view(), name='jdcommodity_detail'),
	url(r'^jdcommodity/(?P<pk>[\d]+)/map/create/$', JdcommoditymapCreateView.as_view(), name='jdcommoditymap_create'),

	#tmcommodity
	url(r'^tmcommodity/$', TmcommodityListView.as_view(), name='tmcommodity_list'),
	url(r'^tmcommodity/(?P<pk>[\w\+]+)/$', TmcommodityDetailView.as_view(), name='tmcommodity_detail'),
	url(r'^tmcommodity/(?P<pk>[\w\+]+)/map/create/$', TmcommoditymapCreateView.as_view(), name='tmcommoditymap_create'),

	#task
	url(r'^task/$', TaskListView.as_view(), name='task_list'),
	url(r'^task/(?P<pk>[\d]+)/$', TaskDetailView.as_view(), name='task_detail'),
	url(r'^task/(?P<pk>[\d]+)/delete/$', TaskDeleteView.as_view(), name='task_delete'),
	url(r'^task/(?P<pk>[\d]+)/revert/$', TaskRevertView.as_view(), name='task_revert'),
	url(r'^task/(?P<pk>[\d]+)/clear/$', TaskClearView.as_view(), name='task_clear'),
	url(r'^task/(?P<pk>[\d]+)/settle/$', TaskSettleView.as_view(), name='task_settle'),
	url(r'^task/(?P<pk>[\d]+)/previous/$', TaskPreviousView.as_view(), name='task_previous'),
	url(r'^task/(?P<pk>[\d]+)/next/$', TaskNextView.as_view(), name='task_next'),
	url(r'^task/(?P<pk>[\d]+)/clear/bill/$', TaskClearBillView.as_view(), name='task_clear_bill'),
	url(r'^task/(?P<pk>[\d]+)/invoice/$', TaskInvoiceView.as_view(), name='task_invoice'),
	url(r'^task/(?P<pk>[\d]+)/profit/$', TaskProfitView.as_view(), name='task_profit'),

	#tmorder
	url(r'^tmorder/change/$', TmorderChangeView.as_view(), name='tmorder_change'),
	url(r'^tmorder/compensate/$', TmorderCompensateView.as_view(), name='tmorder_compensate'),
	url(r'^tmorder/return/$', TmorderReturnView.as_view(), name='tmorder_return'),
	url(r'^tmorder/wechat/fake/$', TmorderWechatFakeView.as_view(), name='tmorder_wechat_fake'),
	url(r'^tmorder/(?P<pk>[\d]+)/$', TmorderDetailViewRead.as_view(), name='tmorder_detail_read'),
	url(r'^tmorder/rebate/$', TmorderRebateView.as_view(), name='tmorder_rebate'),
	url(r'^tmorder/collect/margin/$', TmorderCollectMarginView.as_view(), name='tmorder_collect_margin'),

	#jdorder
	url(r'^jdorder/change/$', JdorderChangeView.as_view(), name='jdorder_change'),
	url(r'^jdorder/compensate/$', JdorderCompensateView.as_view(), name='jdorder_compensate'),
	url(r'^jdorder/return/$', JdorderReturnView.as_view(), name='jdorder_return'),
	url(r'^jdorder/wechat/fake/$', JdorderWechatFakeView.as_view(), name='jdorder_wechat_fake'),
	url(r'^jdorder/(?P<pk>[\d]+)/$', JdorderDetailViewRead.as_view(), name='jdorder_detail_read'),
	url(r'^jdorder/rebate/$', JdorderRebateView.as_view(), name='jdorder_rebate'),
	url(r'^jdorder/collect/margin/$', JdorderCollectMarginView.as_view(), name='jdorder_collect_margin'),

	#misc
	url(r'^misc/daily_task/$', DailyTaskView.as_view(), name='daily_task'),
	url(r'^misc/retail/$', RetailView.as_view(), name='retail'),
	url(r'^misc/change/$', ChangeView.as_view(), name='change'),
	url(r'^misc/commodity/change/repository/$', ChangeRepositoryView.as_view(), name='change_repository'),
	url(r'^misc/receivable/commodity/$', ReceivableCommodityView.as_view(), name='receivable_commodity'),
	url(r'^misc/return/to/supplier/$', ReturnToSupplierView.as_view(), name='return_to_supplier'),
	url(r'^misc/change/with/supplier/$', ChangeWithSupplierView.as_view(), name='change_with_supplier'),

	#purchase
	url(r'^misc/purchase/default/$', PurchaseView.as_view(), name='purchase'),
	url(r'^misc/purchase/tfg/$', TfgPurchaseView.as_view(), name='tfg_purchase'),
	url(r'^misc/purchase/tfg/low/inventory/$', TfgLowInventoryListView.as_view(), name='tfg_low_inventory'),
	url(r'^misc/purchase/yst/$', YstPurchaseView.as_view(), name='yst_purchase'),
	url(r'^misc/purchase/kml/$', KmlPurchaseView.as_view(), name='kml_purchase'),
	url(r'^misc/purchase/other/$', OtherPurchaseView.as_view(), name='other_purchase'),
	url(r'^misc/purchase/append/$', AppendPurchaseView.as_view(), name='append_purchase'),
	url(r'^misc/purchase/trans/shipment/$', TransShipmentView.as_view(), name='trans_shipment'),
	url(r'^purchase/jdorder/$', JdorderPurchaseView.as_view(), name='jdorder_purchase'),
	url(r'^purchase/jdorder/trans/shipment/$', JdorderTransShipmentView.as_view(), name='jdorder_trans_shipment'),
	url(r'^purchase/tmorder/$', TmorderPurchaseView.as_view(), name='tmorder_purchase'),
	url(r'^purchase/tmorder/trans/shipment/$', TmorderTransShipmentView.as_view(), name='tmorder_trans_shipment'),

	#calibration
	url(r'^misc/daily/calibration/$', DailyCalibrationView.as_view(), name='daily_calibration'),
	url(r'^misc/manual/calibration/$', ManualCalibrationView.as_view(), name='manual_calibration'),
	url(r'^misc/daily/calibration/match/$', DailyCalibrationMatchView.as_view(), name='daily_calibration_match'),
	url(r'^calibration/(?P<repository>[\d]+)/inferior/$', InferiorCalibrationView.as_view(), name='inferior_calibration'),

	#misc
	url(r'^misc/pay/wechat/recruit/bonus/$', PayWechatRecruitBonusView.as_view(), name='pay_wechat_recruit_bonus'),
	url(r'^misc/operation/account/pay/$', OperationAccountPayView.as_view(), name='operation_account_pay'),
	url(r'^misc/operation/account/receive/$', OperationAccountReceiveView.as_view(), name='operation_account_receive'),

	#chore
	url(r'^chore/$', ChoreListView.as_view(), name='chore_list'),

	#express
	url(r'^express/(?P<id>[\d]+)/$', ExpressListView.as_view(), name='express_list'),
	url(r'^express/clear/$', ExpressClearView.as_view(), name='express_clear'),

	#calibration_history
	url(r'^calibration_history/$', CalibrationHistoryListView.as_view(), name='calibration_history_list'),
]
