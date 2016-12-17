import markdown

from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from simple_history.models import HistoricalRecords


MARKUP_CHOICES = [
    ['markdown', 'Markdown'],
    ['html', 'HTML'],
]

AFFILIATE_ID = 'wtsr-20'


def asin_to_html(line):
    params = [s.strip() for s in line.split(' ')[1:]]
    asin = params.pop(0)

    link_url = 'http://www.amazon.com/dp/{}/?tag={}'.format(
        asin, AFFILIATE_ID)

    image_template = (
        '//ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN={}'
        '&Format=_SL{}_&ID=AsinImage&MarketPlace=US'
        '&ServiceVersion=20070822&WS=1&tag={}')

    return (
        '<a href="{}" class="amazon-thumbnail" target="_blank">'
        '<img src="{}" data-2x="{}"></img>'
        '</a>').format(
            link_url,
            image_template.format(asin, '250', AFFILIATE_ID),
            image_template.format(asin, '500', AFFILIATE_ID)
        )


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

    title = models.CharField(
        'Title', max_length=255)
    title_short = models.CharField(
        'Short title', max_length=255, null=True, blank=True)
    image = models.CharField(
        'Image', max_length=255, null=True, blank=True)
    if_you_like = models.CharField(
        'If you like', max_length=255, null=True, blank=True)
    slug = models.SlugField(
        'Slug', unique=True, max_length=255)
    description = models.CharField(
        'Description', max_length=160, null=True, blank=True)
    content = models.TextField('Content')

    class Meta:
        ordering = ['-published_at', '-modified_at']

    def __unicode__(self):
        return self.title

    def __str__(self):
        published = 'Unpublished: ' if not self.published_at else ''
        return "{}{}".format(published, self.title)

    @property
    def published(self):
        return self.published_at is not None

    @property
    def content_html(self):
        content = process_asin(self.content)

        if self.markup == 'markdown':
            return markdown.markdown(content)

        return content

    @property
    def canonical_url(self):
        return "http://wheretostartreading.com/articles/{}/".format(self.slug)

    def get_absolute_url(self):
        return reverse('blog.views.article', args=[self.slug])


@receiver(post_save)
def post_model_save(sender, instance, **kwargs):
    """
    Clear cache when any kind of Model is saved
    """
    cache.clear()
