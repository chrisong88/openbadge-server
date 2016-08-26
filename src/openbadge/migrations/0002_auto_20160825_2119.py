# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('openbadge', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meeting',
            name='start_time',
            field=models.DecimalField(null=True, max_digits=20, decimal_places=3, blank=True),
        ),
    ]
