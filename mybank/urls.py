from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

from django.contrib import admin
admin.autodiscover()

class HomeView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        return {'title': 'Welcome to YS Bank!'}

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mybank.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^atm/', include('atm.urls')),
    url(r'^bank_service/', include('bank_service.urls')),
    url(r'^shopping/', include('shopping.urls')),
    url(r'^$', HomeView.as_view(), name='home'),
)
