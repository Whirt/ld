# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-17 10:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webauction', '0006_auto_20180617_1225'),
    ]

    operations = [
        migrations.AddField(
            model_name='followedauction',
            name='isActive',
            field=models.BooleanField(default=True),
        ),
    ]