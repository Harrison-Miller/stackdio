# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-11-14 22:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('formulas', '0003_0_8_0_migrations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='formula',
            name='status',
        ),
        migrations.RemoveField(
            model_name='formula',
            name='status_changed',
        ),
        migrations.RemoveField(
            model_name='formula',
            name='status_detail',
        ),
    ]
