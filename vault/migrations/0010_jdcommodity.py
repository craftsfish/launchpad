# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-01 10:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0009_auto_20180501_1121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Jdcommodity',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False, verbose_name=b'\xe4\xba\xac\xe4\xb8\x9c\xe5\x95\x86\xe5\x93\x81\xe7\xbc\x96\xe7\xa0\x81')),
                ('since', models.DateTimeField(verbose_name=b'\xe7\x94\x9f\xe6\x95\x88\xe6\x97\xb6\xe9\x97\xb4')),
                ('items', models.ManyToManyField(to='vault.Item', verbose_name=b'\xe7\x89\xa9\xe5\x93\x81')),
            ],
        ),
    ]
