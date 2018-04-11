from django.conf.urls import url
from organization_views import *
from supplier_views import *
from item_views import *

urlpatterns = [
	#organization
	url(r'^organization/$', OrganizationListView.as_view(), name='organization_list'),
	url(r'^organization/(?P<pk>[\d]+)/$', OrganizationDetailView.as_view(), name='organization_detail'),

	#supplier
	url(r'^supplier/$', SupplierListView.as_view(), name='supplier_list'),

	#item
	url(r'^item/$', ItemListView.as_view(), name='item_list'),
]
