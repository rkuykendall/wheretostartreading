from datetime import datetime

from django.http import Http404
from django.shortcuts import render
from .models import Article


def home(request):
    articles = Article.objects.filter(published_at__lte=datetime.now()).order_by('-modified_at')
    return render(request, 'home.html', {'articles': articles})


def article(request, slug):
    try:
        articles = Article.objects.filter(published_at__lte=datetime.now())
        article = Article.objects.get(slug=slug)
    except Article.DoesNotExist:
        raise Http404("Poll does not exist")

    return render(
        request, 'article.html', {'article': article, 'articles': articles})
