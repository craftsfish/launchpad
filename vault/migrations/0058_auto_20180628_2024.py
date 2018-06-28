# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-28 12:24
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0057_organization_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
