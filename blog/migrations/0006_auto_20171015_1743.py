# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-10-15 17:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_auto_20170612_1924'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='if_you_like',
        ),
        migrations.RemoveField(
            model_name='historicalarticle',
            name='if_you_like',
        ),
    ]