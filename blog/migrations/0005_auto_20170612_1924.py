# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-06-12 19:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_auto_20161228_0028'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='disqus_src',
            field=models.TextField(blank=True, null=True, verbose_name='Disqus override source'),
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='disqus_src',
            field=models.TextField(blank=True, null=True, verbose_name='Disqus override source'),
        ),
    ]
