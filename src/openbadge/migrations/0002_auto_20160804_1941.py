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
            name='metadata',
            field=models.OneToOneField(related_name='none', null=True, to='openbadge.Event'),
        ),
    ]
