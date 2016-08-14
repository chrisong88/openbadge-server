# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('openbadge', '0002_auto_20160804_1941'),
    ]

    operations = [
        migrations.AddField(
            model_name='hub',
            name='meeting',
            field=models.ForeignKey(related_name='hubs', on_delete=django.db.models.deletion.DO_NOTHING, to='openbadge.Meeting', null=True),
        ),
        migrations.AlterField(
            model_name='meeting',
            name='metadata',
            field=models.ForeignKey(related_name='none', on_delete=django.db.models.deletion.PROTECT, default=0, to='openbadge.Event'),
            preserve_default=False,
        ),
    ]
