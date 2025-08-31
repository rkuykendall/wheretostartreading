from django.utils import timezone

from django.http import Http404
from django.shortcuts import render

from .models import Article


def all(request):
    articles = Article.objects.filter(published_at__lte=timezone.now()).all()

    return render(request, "all.html", {"articles": articles})


def home(request):
    articles = (
        Article.objects.filter(published_at__lte=timezone.now())
        .order_by("-published_at")
        .all()
    )

    all = articles

    articles_popular = [a for a in articles if a.featured]
    articles = [a for a in articles if not a.featured]

    articles_published = articles[:5]
    articles = articles[5:]

    articles_modified = sorted(articles, key=lambda x: x.modified_at, reverse=True)

    return render(
        request,
        "home.html",
        {
            "articles": all,
            "articles_popular": articles_popular,
            "articles_published": articles_published,
            "articles_modified": articles_modified,
        },
    )


def article(request, slug):
    try:
        articles = Article.objects.filter(published_at__lte=timezone.now())
        article = Article.objects.get(slug=slug)
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
    return render(request, "article.html", {"article": article, "articles": articles})
