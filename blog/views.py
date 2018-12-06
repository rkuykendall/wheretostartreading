from datetime import datetime

from django.http import Http404
from django.shortcuts import render
from .models import Article


POPULAR = [
    'spider-man',
    'spider-gwen',
    'iron-man',
    'civil-war',
    'secret-wars',
    'spider-verse',
]


def home(request):
    articles = Article.objects \
        .filter(published_at__lte=datetime.now()) \
        .order_by('-published_at') \
        .all()

    articles_popular = [a for a in articles if a.slug in POPULAR]
    articles = [a for a in articles if a.slug not in POPULAR]

    articles_published = articles[:5]
    articles = articles[5:]

    articles_modified = sorted(
        articles, key=lambda x: x.modified_at, reverse=True)

    articles = [a for a in articles if a.slug not in articles_popular]

    return render(request, 'home.html', {
        'articles_popular': articles_popular,
        'articles_published': articles_published,
        'articles_modified': articles_modified,
    })


def article(request, slug):
    try:
        articles = Article.objects.filter(published_at__lte=datetime.now())
        article = Article.objects.get(slug=slug)
    except Article.DoesNotExist:
        raise Http404("Article does not exist")

    return render(
        request, 'article.html', {'article': article, 'articles': articles})
