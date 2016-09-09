# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-08 18:19
from __future__ import unicode_literals

import django.db.models.deletion
import django_extensions.db.fields
from django.db import migrations, models


def forwards_func(apps, schema_editor):
    Volume = apps.get_model('volumes', 'Volume')

    # Get the blueprint volume from the host def
    for volume in Volume.objects.all():
        for blueprint_volume in volume.host.blueprint_host_definition.volumes.all():
            if blueprint_volume.snapshot == volume.snapshot:
                volume.blueprint_volume = blueprint_volume
                volume.save()


def reverse_func(apps, schema_editor):
    Volume = apps.get_model('volumes', 'Volume')

    # Just put the snapshot back in place
    for volume in Volume.objects.all():
        volume.snapshot = volume.blueprint_volume.snapshot
        volume.save()


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0003_0_8_0_migrations'),
        ('volumes', '0001_0_8_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='volume',
            name='stack',
        ),
        migrations.AddField(
            model_name='volume',
            name='blueprint_volume',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='volumes', to='blueprints.BlueprintVolume'),
        ),
        # Populate the blueprint_volumes
        migrations.RunPython(forwards_func, reverse_func),
        # Make them non-nullable
        migrations.AlterField(
            model_name='volume',
            name='blueprint_volume',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='volumes', to='blueprints.BlueprintVolume'),
        ),
        # delete snapshot
        migrations.RemoveField(
            model_name='volume',
            name='snapshot',
        ),
        migrations.AlterField(
            model_name='volume',
            name='host',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='volumes', to='stacks.Host'),
        ),
        migrations.AlterField(
            model_name='volume',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='volume',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
    ]