# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-08 18:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import stackdio.core.fields


def delete_bad_volumes(apps, schema_migration):
    BlueprintVolume = apps.get_model('blueprints', 'BlueprintVolume')

    # Delete any volumes with null snapshots - they are invalid going backwards
    for volume in BlueprintVolume.objects.filter(snapshot=None):
        volume.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0002_0_8_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blueprint',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='blueprint',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),

        migrations.AlterField(
            model_name='blueprintaccessrule',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='blueprintaccessrule',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),

        migrations.AlterField(
            model_name='blueprinthostdefinition',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='blueprinthostdefinition',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AddField(
            model_name='blueprinthostdefinition',
            name='extra_options',
            field=stackdio.core.fields.JSONField(default={}, verbose_name='Extra Options'),
            preserve_default=False,
        ),

        migrations.AlterField(
            model_name='blueprintvolume',
            name='snapshot',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='blueprint_volumes', to='cloud.Snapshot'),
        ),
        migrations.RunPython(lambda a, s: None, delete_bad_volumes),
        migrations.AlterField(
            model_name='blueprintvolume',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='blueprintvolume',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AddField(
            model_name='blueprintvolume',
            name='encrypted',
            field=models.BooleanField(default=False, verbose_name='Encrypted'),
        ),
        migrations.AddField(
            model_name='blueprintvolume',
            name='extra_options',
            field=stackdio.core.fields.JSONField(default={}, verbose_name='Extra Options'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='blueprintvolume',
            name='size_in_gb',
            field=models.IntegerField(null=True, verbose_name='Size in GB'),
        ),
    ]
