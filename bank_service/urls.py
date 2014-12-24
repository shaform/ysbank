from django.conf.urls import patterns, url

from bank_service import views

urlpatterns = patterns('',
    url(r'^$', views.bank_service, name='bank_service'),
    url(r'^data/acct/$', views.account_number, name='data_account_number'),
    url(r'^data/state/$', views.state, name='data_state'),
    url(r'^data/city/([^/]*)/([^/]*)/$', views.city, name='data_city'),
)
