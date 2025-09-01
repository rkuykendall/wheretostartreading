from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import re

from blog.models import Article, RE_ASIN, get_asin_image_urls, _store_asin_images
from blog import amazon_api


class Command(BaseCommand):
    help = "Backfill Amazon product images by scanning articles for ASINs and fetching via PA-API"

    def add_arguments(self, parser):
        parser.add_argument("--refetch", action="store_true", help="Force refetch even if cached recently")
        parser.add_argument("--since-days", type=int, default=None, help="Only scan articles modified within N days")

    @transaction.atomic
    def handle(self, *args, **options):
        qs = Article.objects.all()
        since_days = options.get("since_days")
        if since_days:
            since = timezone.now() - timezone.timedelta(days=since_days)
            qs = qs.filter(modified_at__gte=since)

        count = 0
        found = set()
        for article in qs.iterator():
            for m in RE_ASIN.finditer(article.content or ""):
                asin = m.group(1)
                if asin in found:
                    continue
                found.add(asin)
                if options.get("refetch"):
                    fetched = amazon_api.fetch_paapi_images(asin)
                    if fetched:
                        _store_asin_images(
                            asin,
                            fetched.get("image_url"),
                            fetched.get("image_url_2x"),
                            fetched.get("title"),
                            status="ok",
                        )
                        res = True
                    else:
                        res = False
                else:
                    res = get_asin_image_urls(asin)
                if res:
                    count += 1
                    self.stdout.write(self.style.SUCCESS(f"Cached images for {asin}"))
                else:
                    self.stdout.write(self.style.WARNING(f"No images for {asin}"))

        self.stdout.write(self.style.SUCCESS(f"Done. Updated {count} ASINs."))
