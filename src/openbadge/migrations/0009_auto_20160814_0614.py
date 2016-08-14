# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('openbadge', '0008_auto_20160814_0345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='data',
            field=jsonfield.fields.JSONField(null=True, blank=True),
        ),
    ]
