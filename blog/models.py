import re
import markdown
from datetime import datetime

from django.core.cache import cache
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
RE_ASIN = re.compile(r'ASIN[ ]([0-9A-Z]{10})')
RE_ASINP = re.compile(r'<ASINP[ ]([0-9A-Z]{10})[ ]?([^>]*)>[ ](.*)')
TWITTER_AT = re.compile(r'@([A-Za-z0-9_]+)')
OFFSITE_LINKS = re.compile(r'href=["\']http')
ASIN_LINKS = re.compile(r'href="https://www.amazon.com/dp/([0-9A-Z]{10})')


def asin_to_url(asin):
    return 'https://www.amazon.com/dp/{}/?tag={}'.format(
        asin, AFFILIATE_ID)


def asin_to_image(asin, size):
    return (
        '//ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN={}'
        '&Format=_SL{}_&ID=AsinImage&MarketPlace=US'
        '&ServiceVersion=20070822&WS=1&tag={}').format(
        asin, size, AFFILIATE_ID)


def asinline_to_thumbnail(line, idx):
    params = [s.strip() for s in line.split(' ')[1:]]
    asin = params.pop(0)
    alt = ' '.join(params)

    return ('''
<a href="{url}" title="{alt}">
<div class="card card-amazon" style="width: 10rem;">
  <div class="blocked-wrapper">
    <p class="blocked-message">Amazon cover images may be blocked by Ad Block</p>
    <img class="card-img-top" src="{src}" data-2x="{src2x}" alt="{alt}" />
  </div>
  <div class="card-asin">#{idx}: {alt}</div>
</div>
</a>
    '''.format(
        idx=idx,
        url=asin_to_url(asin),
        src=asin_to_image(asin, 250),
        src2x=asin_to_image(asin, 500),
        alt=alt,
    ))


def asinpline_to_paragraph(line):
    result = RE_ASINP.match(line)
    asin = result.group(1)
    alt = result.group(2)
    text = result.group(3)

    return ('''
<div class="asin-p">
  <div class="asin-p-left">
    <a href="{url}" title="{alt}">
      <img class="asin-p-img" src="{src}" data-2x="{src2x}" alt="{alt}">
    </a>
  </div>
  <div class="asin-p-right"><p>{text}</p></div>
</div>
'''.format(
        url=asin_to_url(asin),
        src=asin_to_image(asin, 250),
        src2x=asin_to_image(asin, 500),
        alt=alt,
        text=text,
    ))


def process_asin_thumbnails(content):
    lines = content.split('\n')
    new_lines = []
    deck_started = False
    idx = 1

    for line in lines:
        if RE_ASIN.match(line):
            if not deck_started:
                idx = 1
                new_lines.append('<div class="card-deck">')
                deck_started = True

            new_lines.append(asinline_to_thumbnail(line, idx))
            idx += 1

        else:
            if deck_started:
                new_lines.append('</div>')
                deck_started = False

            new_lines.append(line)

    if deck_started:
        new_lines.append('</div>')

    return '\n'.join(new_lines)


def process_asin_paragraphs(content):
    return '\n'.join([
        line if not RE_ASINP.match(line)
        else asinpline_to_paragraph(line)
        for line in content.split('\n')
    ])


def process_asin_links(content):
    content = RE_ASIN.sub(
        lambda m: asin_to_url(m.group(1)),
        content)

    return content


def process_twitter_links(content):
    content = TWITTER_AT.sub(
        lambda m: 'https://twitter.com/{}'.format(m.group(1)),
        content)

    return content


def process_link_targets(content):
    content = OFFSITE_LINKS.sub(
        lambda m: 'target="_blank" {}'.format(m.group(0)),
        content)

    return content


def process_asin_tracking(content):
    content = ASIN_LINKS.sub(
        lambda m: 'onClick="trackAsinClick(\'{}\')" {}'.format(
            m.group(1), m.group(0)), content)

    return content


class Article(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()
    featured = models.BooleanField(default=False)

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
    slug = models.SlugField(
        'Slug', unique=True, max_length=255)
    credit = models.CharField(
        'Credit', max_length=255, default='Written by Robert Kuykendall')
    description = models.CharField(
        'Description', max_length=160, null=True, blank=True)
    content = models.TextField('Content')
    disqus_src = models.TextField(
        'Disqus override source', null=True, blank=True)

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
        content = self.content
        content = process_asin_thumbnails(content)
        content = process_asin_paragraphs(content)
        content = process_asin_links(content)
        content = process_twitter_links(content)

        if self.markup == 'markdown':
            content = markdown.markdown(content)

        content = process_link_targets(content)
        content = process_asin_tracking(content)

        return content

    @property
    def related(self, num=4):
        return list(Article.objects.filter(
            published_at__lte=datetime.now()).exclude(
                id=self.id).order_by('?'))[:num]

    @property
    def canonical_url(self):
        return "https://wheretostartreading.com/articles/{}/".format(self.slug)

    def get_absolute_url(self):
        return reverse('blog.views.article', args=[self.slug])


@receiver(post_save)
def post_model_save(sender, instance, **kwargs):
    """
    Clear cache when any kind of Model is saved
    """
    cache.clear()
