import re
import markdown
from typing import Optional, Tuple

from django.core.cache import cache
from django.urls import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from simple_history.models import HistoricalRecords


MARKUP_CHOICES = [
    ["markdown", "Markdown"],
    ["html", "HTML"],
]

AFFILIATE_ID = "wtsr-20"
RE_ASIN = re.compile(r"ASIN[ ]([0-9A-Z]{10})")
RE_ASINP = re.compile(r"<ASINP[ ]([0-9A-Z]{10})[ ]?([^>]*)>[ ](.*)")
TWITTER_AT = re.compile(r"@([A-Za-z0-9_]+)")
OFFSITE_LINKS = re.compile(r'href=["\']http')
ASIN_LINKS = re.compile(r'href="https://www.amazon.com/dp/([0-9A-Z]{10})')


def asin_to_url(asin):
    return "https://www.amazon.com/dp/{}/?tag={}".format(asin, AFFILIATE_ID)


class AmazonProduct(models.Model):
    """Lightweight cache of Amazon product image URLs by ASIN."""

    asin = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    image_url_2x = models.URLField(max_length=500, null=True, blank=True)
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    fetch_status = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.asin}"

    class Meta:
        indexes = [models.Index(fields=["asin"])]


def _get_cached_asin_images(asin: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """Return (image_url, image_url_2x, title) from DB/cache if fresh enough."""
    cache_key = f"asin-images:{asin}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        ap = AmazonProduct.objects.filter(asin=asin).first()
    except Exception:
        ap = None
    if ap and ap.image_url:
        # consider fresh if fetched within 30 days
        if not ap.last_fetched_at or (
            timezone.now() - ap.last_fetched_at
        ).days <= 30:
            data = (ap.image_url, ap.image_url_2x or ap.image_url, ap.title)
            cache.set(cache_key, data, 60 * 60)  # 1 hour
            return data
    return None


def _store_asin_images(
    asin: str, image_url: Optional[str], image_url_2x: Optional[str], title: Optional[str], status: str
) -> Optional[Tuple[str, str, Optional[str]]]:
    try:
        ap, _ = AmazonProduct.objects.get_or_create(asin=asin)
        ap.image_url = image_url
        ap.image_url_2x = image_url_2x
        if title:
            ap.title = title
        ap.last_fetched_at = timezone.now()
        ap.fetch_status = status
        ap.save()
        if image_url:
            data = (image_url, image_url_2x or image_url, title)
            cache.set(f"asin-images:{asin}", data, 60 * 60)
            return data
    except Exception:
        pass
    return None


def get_asin_image_urls(asin: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """Resolve image URLs for an ASIN using DB cache then PA-API; returns (src, src2x, title)."""
    # 1) Cache/DB
    cached = _get_cached_asin_images(asin)
    if cached:
        return cached

    # 2) Try PA-API fetch
    try:
        from . import amazon_api

        fetched = amazon_api.fetch_paapi_images(asin)
        if fetched:
            return _store_asin_images(
                asin,
                fetched.get("image_url"),
                fetched.get("image_url_2x"),
                fetched.get("title"),
                status="ok",
            )
        else:
            # negative cache briefly to avoid hammering on failures
            cache.set(f"asin-images:{asin}", None, 60 * 5)
            _store_asin_images(asin, None, None, None, status="miss")
            return None
    except Exception:
        # On any error, do not break page render
        return None


def get_thumbnail(asin, alt, idx=None):
        asin_formatted = "#{idx}: ".format(idx=idx) if idx else ""

        # Try to resolve images via stored/fetched URLs
        resolved = get_asin_image_urls(asin)
        if resolved:
                src, src2x, title = resolved
                alt_text = alt or title or "Amazon product"
                return """
        <a href="{url}" title="{alt}">
        <div class="card card-amazon" style="width: 10rem;">
            <div class="blocked-wrapper">
                <p class="blocked-message">Amazon cover images may be blocked by Ad Block</p>
                <img class="card-img-top" src="{src}" data-2x="{src2x}" alt="{alt}" />
            </div>
            <div class="card-asin">{asin_formatted}{alt}</div>
        </div>
        </a>
                """.format(
                        asin_formatted=asin_formatted,
                        url=asin_to_url(asin),
                        src=src,
                        src2x=src2x or src,
                        alt=alt_text,
                )

        # Fallback: render link-only card without image
        return """
        <a href="{url}" title="{alt}">
        <div class="card card-amazon" style="width: 10rem;">
            <div class="blocked-wrapper">
                <p class="blocked-message">Image unavailable</p>
            </div>
            <div class="card-asin">{asin_formatted}{alt}</div>
        </div>
        </a>
                """.format(
                asin_formatted=asin_formatted,
                url=asin_to_url(asin),
                alt=alt or "Amazon product",
        )


def asinline_to_thumbnail(line, idx):
    params = [s.strip() for s in line.split(" ")[1:]]
    asin = params.pop(0)
    alt = " ".join(params)

    return get_thumbnail(asin, alt, idx)


def asinpline_to_paragraph(line):
    result = RE_ASINP.match(line)
    asin = result.group(1)
    alt = result.group(2)
    text = markdown.markdown(result.group(3))

    return """
<div class="asin-p">
  <div class="asin-p-left">
    {thumbnail}
  </div>
  <div class="asin-p-right">{text}</div>
</div>
""".format(
        thumbnail=get_thumbnail(asin, alt),
        text=text,
    )


def process_asin_thumbnails(content):
    lines = content.split("\n")
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
                new_lines.append("</div>")
                deck_started = False

            new_lines.append(line)

    if deck_started:
        new_lines.append("</div>")

    return "\n".join(new_lines)


def process_asin_paragraphs(content):
    return "\n".join(
        [
            line if not RE_ASINP.match(line) else asinpline_to_paragraph(line)
            for line in content.split("\n")
        ]
    )


def process_asin_links(content):
    content = RE_ASIN.sub(lambda m: asin_to_url(m.group(1)), content)

    return content


def process_twitter_links(content):
    content = TWITTER_AT.sub(
        lambda m: "https://twitter.com/{}".format(m.group(1)), content
    )

    return content


def process_link_targets(content):
    content = OFFSITE_LINKS.sub(
        lambda m: 'target="_blank" {}'.format(m.group(0)), content
    )

    return content


def process_asin_tracking(content):
    content = ASIN_LINKS.sub(
        lambda m: "onClick=\"trackAsinClick('{}')\" {}".format(m.group(1), m.group(0)),
        content,
    )

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
        default="markdown",
    )

    title = models.CharField("Title", max_length=255)
    title_short = models.CharField("Short title", max_length=255, null=True, blank=True)
    image = models.CharField("Image", max_length=255, null=True, blank=True)
    slug = models.SlugField("Slug", unique=True, max_length=255)
    credit = models.CharField(
        "Credit", max_length=255, default="Written by Robert Kuykendall"
    )
    description = models.CharField("Description", max_length=160, null=True, blank=True)
    content = models.TextField("Content")
    disqus_src = models.TextField("Disqus override source", null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-modified_at"]

    def __unicode__(self):
        return self.title

    def __str__(self):
        published = "Unpublished: " if not self.published_at else ""
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

        if self.markup == "markdown":
            content = markdown.markdown(content)

        content = process_link_targets(content)
        content = process_asin_tracking(content)

        return content

    @property
    def related(self, num=4):
        return list(
            Article.objects.filter(published_at__lte=timezone.now())
            .exclude(id=self.id)
            .order_by("?")
        )[:num]

    @property
    def canonical_url(self):
        return "https://wheretostartreading.com/articles/{}/".format(self.slug)

    def get_absolute_url(self):
        return reverse("blog.views.article", args=[self.slug])


@receiver(post_save)
def post_model_save(sender, instance, **kwargs):
    """
    Clear cache when any kind of Model is saved
    """
    cache.clear()
