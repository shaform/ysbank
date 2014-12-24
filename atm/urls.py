from django.conf.urls import patterns, url

from atm import views

urlpatterns = patterns('',
    url(r'^$', views.atm, name='atm')
)
