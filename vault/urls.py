from django.conf.urls import url
from organization_views import *
from supplier_views import *
from item_views import *
from account_views import *
from transaction_views import *
from jdcommodity_views import *

urlpatterns = [
	#organization
	url(r'^organization/$', OrganizationListView.as_view(), name='organization_list'),
	url(r'^organization/(?P<pk>[\d]+)/$', OrganizationDetailView.as_view(), name='organization_detail'),

	#supplier
	url(r'^supplier/$', SupplierListView.as_view(), name='supplier_list'),

	#item
	url(r'^item/$', ItemListView.as_view(), name='item_list'),

	#account
	url(r'^account/$', AccountListView.as_view(), name='account_list'),
	url(r'^account/(?P<pk>[\d]+)/$', AccountDetailView.as_view(), name='account_detail'),

	#transaction
	url(r'^transaction/$', TransactionListView.as_view(), name='transaction_list'),
	url(r'^transaction/(?P<pk>[\d]+)/$', TransactionDetailView.as_view(), name='transaction_detail'),
	url(r'^transaction/(?P<pk>[\d]+)/change/$', TransactionUpdateView.as_view(), name='transaction_update'),
	url(r'^transaction/(?P<pk>[\d]+)/duplicate/$', TransactionDuplicateView.as_view(), name='transaction_duplicate'),

	#jdcommodity
	url(r'^jdcommodity/$', JdcommodityListView.as_view(), name='jdcommodity_list'),
	url(r'^jdcommodity/(?P<pk>[\d]+)/$', JdcommodityDetailView.as_view(), name='jdcommodity_detail'),
	url(r'^jdcommodity/(?P<pk>[\d]+)/map/create/$', JdcommoditymapCreateView.as_view(), name='jdcommoditymap_create'),

]
