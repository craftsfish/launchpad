# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-19 08:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0047_auto_20180619_1615'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jdorder',
            name='repository',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='vault.Repository'),
        ),
    ]
