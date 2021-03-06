# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-16 14:48
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0002_auto_20180616_1648'),
        ('webauction', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('message_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='messenger.Message')),
                ('rating', models.SmallIntegerField(validators=[django.core.validators.MaxValueValidator(10), django.core.validators.MinValueValidator(1)])),
            ],
            bases=('messenger.message',),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='votes',
            field=models.IntegerField(default=0),
        ),
    ]
