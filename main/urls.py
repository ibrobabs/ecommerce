from django.conf.urls import url
from main import json_views as views 

urlpatterns = [
	url(r'^status_reports/$', views.status_collection, name='status_collection'),
	url(r'^status_reports/(?P<id>[0-9]+)$', views.status_member, name='status_member'),
]