# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-10 01:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_0_8_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(max_length=128, unique=True, verbose_name='Tag')),
            ],
        ),
    ]
