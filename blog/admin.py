from django.contrib import admin

from .models import Article


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_short', 'published_at', 'modified_at', )
    list_filter = ('published_at', )

admin.site.register(Article, ArticleAdmin)
