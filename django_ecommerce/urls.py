from django.conf.urls import include, url 
from payments import views
from main import views as main_views
from contact import views as contact_views
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', main_views.index, name='home'),
    url(r'^home/', main_views.index, name='home'),
    url(r'^pages/', include('django.contrib.flatpages.urls')),
    url(r'^contact/', contact_views.contact, name='contact'),
    url(r'^report$', main_views.report, name="report"),


    url(r'^sign_in$', views.sign_in, name='sign_in'),
    url(r'^sign_out$', views.sign_out, name='sign_out'),
    url(r'^register$', views.register, name='register'),
    url(r'^edit$', views.edit, name='edit'),

    url(r'^api/v1/', include('main.urls')),
]