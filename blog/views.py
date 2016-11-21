from django.shortcuts import render
from .models import Article


def home(request):
    articles = Article.objects.filter(published_at__isnull=False)
    return render(request, 'home.html', {'articles': articles})


def article(request, slug):
    article = Article.objects.get(slug=slug)
    return render(request, 'article.html', {'article': article})
