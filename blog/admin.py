from django.contrib import admin
from django import forms

from .models import Article


class ArticleModelForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        exclude = ()
        model = Article


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'modified_at', )
    list_filter = ('published_at', )
    form = ArticleModelForm

admin.site.register(Article, ArticleAdmin)
