# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('openbadge', '0006_auto_20160812_1045'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meeting',
            name='metadata',
            field=models.ForeignKey(related_name='none', to='openbadge.Event', null=True),
        ),
    ]
