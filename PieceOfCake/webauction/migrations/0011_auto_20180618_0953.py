# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-18 07:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webauction', '0010_auction_premium_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='feedback',
            field=models.IntegerField(default=0),
        ),
    ]
