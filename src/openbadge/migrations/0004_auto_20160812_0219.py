# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('openbadge', '0003_auto_20160812_0214'),
    ]

    operations = [
        migrations.RenameField(
            model_name='hub',
            old_name='meeting',
            new_name='current_meeting',
        ),
    ]
