import markdown

from django.db import models
from django.core.urlresolvers import reverse

from simple_history.models import HistoricalRecords


MARKUP_CHOICES = [
    ['markdown', 'Markdown'],
    ['html', 'HTML'],
]

AFFILIATE_ID = 'roberkuyke-20'


def asin_to_html(line):
    params = [s.strip() for s in line.split(' ')[1:]]
    asin = params.pop(0)

    link_url = 'http://www.amazon.com/dp/{}/?tag={}'.format(
        asin, AFFILIATE_ID)

    image_url = (
        '//ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN={}'
        '&Format=_SL500_&ID=AsinImage&MarketPlace=US'
        '&ServiceVersion=20070822&WS=1&tag={}').format(
            asin, AFFILIATE_ID)

    return (
        '<a href="{}" class="amazon-thumbnail" target="_blank">'
        '<img src="{}"></img>'
        '</a>').format(link_url, image_url)


def process_asin(content):
    processed = []

    for line in content.split('\n'):
        if line[:4] == 'ASIN':
            processed.append(asin_to_html(line))
        else:
            processed.append(line)

    return '\n'.join(processed)


class Article(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    markup = models.CharField(
        max_length=10,
        choices=MARKUP_CHOICES,
        default='markdown',
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()

    class Meta:
        ordering = ['-published_at', '-modified_at']

    def __unicode__(self):
        return self.title

    def __str__(self):
        published = 'Unpublished: ' if not self.published_at else ''
        return "{}{}".format(published, self.title)

    @property
    def content_html(self):
        content = process_asin(self.content)

        if self.markup == 'markdown':
            return markdown.markdown(content)

        return content

    @property
    def canonical_url(self):
        return "http://wheretostartreading.com/{}/".format(self.slug)

    def get_absolute_url(self):
        return reverse('blog.views.article', args=[self.slug])
