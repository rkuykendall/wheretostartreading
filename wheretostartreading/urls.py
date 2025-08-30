from django.utils import timezone

from django.urls import include, re_path
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.urls import reverse
from django.http import HttpResponse

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
            'queryset': Article.objects.filter(
                published_at__lte=timezone.now()),
            'date_field': 'modified_at',
        }, priority=0.6),
    'homepage': HomepageSitemap,
}

urlpatterns = [
    re_path(r'^gauntlet/', admin.site.urls),
    re_path(r'', include('blog.urls')),
    re_path(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),
    re_path(r'^robots.txt$', lambda r: HttpResponse(
        (
            "User-agent: * \n"
            "Disallow: \n"
            "Sitemap: https://wheretostartreading.com/sitemap.xml"
        ),
        content_type="text/plain"))
]
