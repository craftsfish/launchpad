# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-22 05:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0021_auto_20180520_2156'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='cleared',
            field=models.BooleanField(default=True, verbose_name=b'\xe7\xbb\x93\xe7\xae\x97'),
        ),
        migrations.AddField(
            model_name='task',
            name='settled',
            field=models.BooleanField(default=True, verbose_name=b'\xe4\xba\xa4\xe5\x89\xb2'),
        ),
    ]
