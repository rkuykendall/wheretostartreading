from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^all/$', views.all, name='all'),
    url(r'^$', views.home, name='home'),
    url(r'^articles/(?P<slug>[a-z\-]+)/$', views.article, name='article'),
]
