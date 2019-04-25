from django.contrib import admin
from django.forms import Textarea
from django.db import models

from .models import Article


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_short', 'published_at', 'modified_at', )
    list_filter = ('published_at', )

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 70, 'cols': 120})},
    }


admin.site.register(Article, ArticleAdmin)
