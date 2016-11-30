from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.core.urlresolvers import reverse

from blog.models import Article

class HomepageSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home']

    def location(self, item):
        return reverse(item)

sitemaps = {
    'blog': GenericSitemap({
            'queryset': Article.objects.all(),
            'date_field': 'modified_at',
        }, priority=0.6),
    'homepage': HomepageSitemap,
}

urlpatterns = [
    url(r'^gauntlet/', admin.site.urls),
    url(r'', include('blog.urls')),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),
]
