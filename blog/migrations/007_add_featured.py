# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2021-11-04 20:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_auto_20171015_1743'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='featured',
            field=models.BooleanField(default=False),
        ),
    ]

