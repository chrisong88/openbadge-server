# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('openbadge', '0005_auto_20160812_1026'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meeting',
            name='metadata',
            field=models.ForeignKey(related_name='none', on_delete=django.db.models.deletion.PROTECT, to='openbadge.Event', null=True),
        ),
    ]
