# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpenBadgeUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=30, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, verbose_name='username')),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(unique=True, max_length=254, verbose_name='email address', db_index=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('key', models.CharField(db_index=True, unique=True, max_length=10, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('type', models.CharField(max_length=64)),
                ('log_timestamp', models.DecimalField(max_digits=20, decimal_places=3)),
                ('log_index', models.IntegerField()),
                ('data', jsonfield.fields.JSONField(null=True, blank=True)),
            ],
            options={
                'ordering': ['log_timestamp'],
                'get_latest_by': 'log_index',
            },
        ),
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField()),
                ('last_activity_update', models.DecimalField(max_digits=20, decimal_places=3)),
                ('last_log_index', models.IntegerField(default=-1)),
                ('members', jsonfield.fields.JSONField(default={}, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Hub',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('key', models.CharField(db_index=True, unique=True, max_length=10, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=64)),
                ('su', models.BooleanField(default=False)),
                ('uuid', models.CharField(unique=True, max_length=64, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('key', models.CharField(db_index=True, unique=True, max_length=10, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('version', models.DecimalField(max_digits=5, decimal_places=2)),
                ('uuid', models.CharField(unique=True, max_length=64, db_index=True)),
                ('is_active', models.BooleanField(default=False)),
                ('start_time', models.DecimalField(max_digits=20, decimal_places=3)),
                ('end_time', models.DecimalField(null=True, max_digits=20, decimal_places=3, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('key', models.CharField(db_index=True, unique=True, max_length=10, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=64)),
                ('email', models.EmailField(max_length=254, blank=True)),
                ('badge', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('key', models.CharField(db_index=True, unique=True, max_length=10, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=64)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='member',
            name='project',
            field=models.ForeignKey(related_name='members', to='openbadge.Project'),
        ),
        migrations.AddField(
            model_name='meeting',
            name='project',
            field=models.ForeignKey(related_name='meetings', to='openbadge.Project'),
        ),
        migrations.AddField(
            model_name='hub',
            name='current_meeting',
            field=models.ForeignKey(related_name='hubs', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='openbadge.Meeting', null=True),
        ),
        migrations.AddField(
            model_name='hub',
            name='project',
            field=models.ForeignKey(related_name='hubs', to='openbadge.Project', null=True),
        ),
        migrations.AddField(
            model_name='history',
            name='hub',
            field=models.ForeignKey(related_name='histories', on_delete=django.db.models.deletion.SET_NULL, to='openbadge.Hub', null=True),
        ),
        migrations.AddField(
            model_name='history',
            name='meeting',
            field=models.ForeignKey(related_name='histories', to='openbadge.Meeting', null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='hub',
            field=models.ForeignKey(related_name='events', on_delete=django.db.models.deletion.SET_NULL, to='openbadge.Hub', null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='meeting',
            field=models.ForeignKey(related_name='events', to='openbadge.Meeting'),
        ),
        migrations.AlterUniqueTogether(
            name='member',
            unique_together=set([('badge', 'project')]),
        ),
        migrations.AlterIndexTogether(
            name='history',
            index_together=set([('meeting', 'hub')]),
        ),
        migrations.AlterIndexTogether(
            name='event',
            index_together=set([('log_index', 'hub', 'meeting')]),
        ),
    ]
