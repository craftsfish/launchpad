from django.conf.urls import url
from organization_views import *

urlpatterns = [
	#organization
	url(r'^organization/$', OrganizationListView.as_view(), name='organization_list'),
]
