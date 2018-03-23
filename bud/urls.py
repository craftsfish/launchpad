from django.conf.urls import url

from account_views import *
from task_views import *
from transaction_views import *
from split_views import *

urlpatterns = [
    url(r'^account/$', AccountListView.as_view(), name='account_index'),
    url(r'^account/(?P<pk>[\d]+)/$', AccountDetailView.as_view(), name='account_detail'),
    url(r'^account/(?P<pk>[\d]+)/change/$', AccountUpdateView.as_view(), name='account_update'),
    url(r'^account/(?P<pk>[\d]+)/create/$', AccountCreateView.as_view(), name='account_create'),
    url(r'^account/(?P<pk>[\d]+)/delete/$', AccountDeleteView.as_view(), name='account_delete'),
    url(r'^task/$', TaskListView.as_view(), name='task_index'),
    url(r'^task/create/$', TaskCreateView.as_view(), name='task_create'),
    url(r'^task/(?P<pk>[\d]+)/$', TaskDetailView.as_view(), name='task_detail'),
    url(r'^transaction/(?P<pk>[\d]+)/$', TransactionDetailView.as_view(), name='transaction_detail'),
    url(r'^split/(?P<pk>[\d]+)/$', SplitDetailView.as_view(), name='split_detail'),
]
