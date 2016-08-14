# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('openbadge', '0004_auto_20160812_0219'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hub',
            name='current_meeting',
            field=models.ForeignKey(related_name='hubs', on_delete=django.db.models.deletion.DO_NOTHING, blank=True, to='openbadge.Meeting', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='member',
            unique_together=set([('badge', 'project')]),
        ),
    ]
