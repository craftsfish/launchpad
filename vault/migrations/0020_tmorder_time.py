# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-20 13:55
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0019_tmorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='tmorder',
            name='time',
            field=models.DateTimeField(default=datetime.datetime(2018, 5, 20, 13, 55, 1, 409130, tzinfo=utc)),
        ),
    ]
