from django.conf.urls import patterns, url

from shopping import views

urlpatterns = patterns('',
    url(r'^$', views.shopping, name='shopping'),
)
