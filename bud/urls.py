from django.conf.urls import url

from views import *

urlpatterns = [
    url(r'^$', AccountListView.as_view(), name='index'),
]
