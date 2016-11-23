import markdown

from django.db import models
from django.core.urlresolvers import reverse

from simple_history.models import HistoricalRecords


MARKUP_CHOICES = [
    ['markdown', 'Markdown'],
    ['html', 'HTML'],
]


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
        return "Article: {}".format(self.title)

    @property
    def content_html(self):
        if self.markup == 'markdown':
            return markdown.markdown(self.content)

        return self.content

    @property
    def canonical_url(self):
        return "http://wheretostartreading.com/{}/".format(self.slug)

    def get_absolute_url(self):
        return reverse('blog.views.article', args=[self.slug])
