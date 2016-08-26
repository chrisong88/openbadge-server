# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('openbadge', '0002_auto_20160825_2119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='history',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='history',
            name='last_activity_update',
            field=models.IntegerField(default=-1),
        ),
        migrations.AlterUniqueTogether(
            name='event',
            unique_together=set([('log_index', 'hub', 'meeting')]),
        ),
    ]
