from django.conf.urls import include, url
from . import views
from django.views.generic.base import TemplateView

urlpatterns = [
    # No-Groups URLS
    url(r'^projects$', views.projects, name='projects'),
    url(r'^(?P<project_key>\w+)/meetings$', views.meetings, name='meetings'),
    url(r'^(?P<project_key>\w+)/hubs$', views.hubs, name='hubs'),
    url(r'^(?P<project_key>\w+)/members', views.put_members, name='members'),
]