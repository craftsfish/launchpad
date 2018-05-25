# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-25 06:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0025_account_repository'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='vault.Supplier', verbose_name=b'\xe4\xbe\x9b\xe5\xba\x94\xe5\x95\x86'),
        ),
    ]
