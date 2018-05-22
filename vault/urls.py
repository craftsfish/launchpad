from django.conf.urls import url
from supplier_views import *
from item_views import *
from account_views import *
from transaction_views import *
from jdcommodity_views import *
from tmcommodity_views import *
from task_views import *
from shipping_views import *

urlpatterns = [
	#supplier
	url(r'^supplier/$', SupplierListView.as_view(), name='supplier_list'),

	#item
	url(r'^item/$', ItemListView.as_view(), name='item_list'),
	url(r'^item/(?P<pk>[\d]+)/organization/(?P<org>[\d]+)/$', ItemDetailView.as_view(), name='item_detail'),

	#account
	url(r'^account/$', AccountListView.as_view(), name='account_list'),
	url(r'^account/(?P<pk>[\d]+)/$', AccountDetailView.as_view(), name='account_detail'),

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
	url(r'^task/(?P<pk>[\d]+)/$', TaskDetailView.as_view(), name='task_detail'),
	url(r'^task/(?P<pk>[\d]+)/delete/$', TaskDeleteView.as_view(), name='task_delete'),

	#misc
	url(r'^shipping/(?P<type>\d)/(?P<task_id>[\d]+)/$', ShippingInCreateView.as_view(), name='shipping_in_create'),
]
