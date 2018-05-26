# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-26 03:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0030_auto_20180526_1129'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='commodity',
            options={'ordering': ['supplier', 'name']},
        ),
        migrations.RemoveField(
            model_name='tmcommoditymap',
            name='items',
        ),
        migrations.AddField(
            model_name='tmcommoditymap',
            name='commodities',
            field=models.ManyToManyField(to='vault.Commodity', verbose_name=b'\xe5\x95\x86\xe5\x93\x81'),
        ),
    ]
