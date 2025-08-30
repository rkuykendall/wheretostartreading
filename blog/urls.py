from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^all/$', views.all, name='all'),
    re_path(r'^$', views.home, name='home'),
    re_path(r'^articles/(?P<slug>[a-z\-]+)/$', views.article, name='article'),
]
