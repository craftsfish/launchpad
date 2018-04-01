# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bud', '0012_auto_20180331_0901'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commodity',
            name='supplier',
            field=models.ForeignKey(to='bud.Supplier'),
        ),
    ]
