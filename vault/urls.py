from django.conf.urls import url
from organization_views import *
from supplier_views import *
from item_views import *
from account_views import *
from transaction_views import *

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
	url(r'^transaction/(?P<pk>[\d]+)/$', TransactionDetailView.as_view(), name='transaction_detail'),
	url(r'^transaction/(?P<pk>[\d]+)/change$', TransactionUpdateView.as_view(), name='transaction_update'),
]
