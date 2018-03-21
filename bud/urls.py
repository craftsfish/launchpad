from django.conf.urls import url

from views import *

urlpatterns = [
    url(r'^$', AccountListView.as_view(), name='index'),
    url(r'^account/(?P<pk>[\d]+)/$', AccountDetailView.as_view(), name='account_detail'),
    url(r'^account/(?P<pk>[\d]+)/change/$', AccountUpdateView.as_view(), name='account_update'),
    url(r'^account/(?P<pk>[\d]+)/createchild/$', AccountCreateChildView.as_view(), name='account_create_child'),
]
