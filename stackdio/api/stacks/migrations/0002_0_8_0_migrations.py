# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-08 18:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import model_utils.fields


def fix_fields_forwards(apps, schema_editor):
    Stack = apps.get_model('stacks', 'Stack')
    Host = apps.get_model('stacks', 'Host')

    # Just set all the activities to be idle.
    for stack in Stack.objects.all():
        stack.activity = ''
        stack.save()

    for host in Host.objects.all():
        host.activity = ''
        host.save()


def fix_fields_reverse(apps, schema_editor):
    Stack = apps.get_model('stacks', 'Stack')

    # Host states are already set in 0.8, no need to change them when going backwards.
    for stack in Stack.objects.all():
        stack.status = 'finished'
        stack.save()


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0001_0_8_initial'),
        ('formulas', '0002_0_8_0_migrations'),
    ]

    operations = [
        # Host things
        migrations.RemoveField(
            model_name='host',
            name='availability_zone',
        ),
        migrations.RemoveField(
            model_name='host',
            name='cloud_image',
        ),
        migrations.RemoveField(
            model_name='host',
            name='instance_size',
        ),
        migrations.RemoveField(
            model_name='host',
            name='subnet_id',
        ),
        migrations.AlterField(
            model_name='host',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='host',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.RenameField(
            model_name='host',
            old_name='provider_dns',
            new_name='provider_public_dns',
        ),
        migrations.AlterField(
            model_name='host',
            name='provider_public_dns',
            field=models.CharField(max_length=64, null=True, verbose_name=b'Provider Public DNS'),
        ),
        migrations.AlterField(
            model_name='host',
            name='provider_private_dns',
            field=models.CharField(max_length=64, null=True, verbose_name=b'Provider Private DNS'),
        ),
        migrations.AddField(
            model_name='host',
            name='provider_public_ip',
            field=models.GenericIPAddressField(blank=True, null=True, verbose_name=b'Provider Public IP'),
        ),
        migrations.AlterField(
            model_name='host',
            name='provider_private_ip',
            field=models.GenericIPAddressField(blank=True, null=True, verbose_name=b'Provider Private IP'),
        ),
        migrations.RemoveField(
            model_name='host',
            name='state_reason',
        ),
        migrations.RemoveField(
            model_name='host',
            name='status_changed',
        ),
        migrations.RemoveField(
            model_name='host',
            name='status_detail',
        ),
        migrations.RenameField(
            model_name='host',
            old_name='status',
            new_name='activity',
        ),
        migrations.AlterField(
            model_name='host',
            name='activity',
            field=models.CharField(blank=True, choices=[(b'unknown', b'unknown'), (b'queued', b'queued'), (b'launching', b'launching'), (b'provisioning', b'provisioning'), (b'orchestrating', b'orchestrating'), (b'', b''), (b'pausing', b'pausing'), (b'paused', b'paused'), (b'resuming', b'resuming'), (b'terminating', b'terminating'), (b'terminated', b'terminated'), (b'executing', b'executing'), (b'dead', b'dead')], default=b'queued', max_length=32, verbose_name=b'Activity'),
        ),

        # Stack things
        migrations.AlterField(
            model_name='stack',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='stack',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.RemoveField(
            model_name='stack',
            name='status_changed',
        ),
        migrations.RenameField(
            model_name='stack',
            old_name='status',
            new_name='activity',
        ),
        migrations.AlterField(
            model_name='stack',
            name='activity',
            field=models.CharField(blank=True, choices=[(b'unknown', b'unknown'), (b'queued', b'queued'), (b'launching', b'launching'), (b'provisioning', b'provisioning'), (b'orchestrating', b'orchestrating'), (b'', b''), (b'pausing', b'pausing'), (b'paused', b'paused'), (b'resuming', b'resuming'), (b'terminating', b'terminating'), (b'terminated', b'terminated'), (b'executing', b'executing'), (b'dead', b'dead')], default=b'queued', max_length=32, verbose_name=b'Activity'),
        ),
        migrations.AlterModelOptions(
            name='stack',
            options={'default_permissions': ('delete', 'execute', 'pause', 'launch', 'admin', 'create', 'resume', 'terminate', 'update', 'ssh', 'orchestrate', 'provision', 'view'), 'ordering': ('title',)},
        ),

        # Stack Command things
        migrations.AlterField(
            model_name='stackcommand',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='stackcommand',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='stackcommand',
            name='status',
            field=model_utils.fields.StatusField(default=b'waiting', max_length=100, no_check_for_status=True, verbose_name='status'),
        ),

        # Stack History things
        migrations.AlterField(
            model_name='stackhistory',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='stackhistory',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.RemoveField(
            model_name='stackhistory',
            name='status',
        ),
        migrations.RemoveField(
            model_name='stackhistory',
            name='event',
        ),
        migrations.RemoveField(
            model_name='stackhistory',
            name='level',
        ),
        migrations.RemoveField(
            model_name='stackhistory',
            name='status_changed',
        ),
        migrations.RenameField(
            model_name='stackhistory',
            old_name='status_detail',
            new_name='message',
        ),
        migrations.AlterField(
            model_name='stackhistory',
            name='message',
            field=models.CharField(max_length=256, verbose_name=b'Message'),
        ),

        # New things
        migrations.CreateModel(
            name='ComponentMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('status', models.CharField(choices=[(b'succeeded', b'succeeded'), (b'unknown', b'unknown'), (b'failed', b'failed'), (b'running', b'running'), (b'cancelled', b'cancelled'), (b'queued', b'queued')], default=b'queued', max_length=32, verbose_name=b'Status')),
                ('health', models.CharField(choices=[(b'healthy', b'healthy'), (b'unknown', b'unknown'), (b'unstable', b'unstable'), (b'unhealthy', b'unhealthy')], default=b'unknown', max_length=32, verbose_name=b'Health')),
                ('formula_component', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metadatas', to='formulas.FormulaComponent')),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='component_metadatas', to='stacks.Host')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
        ),

        # Fix fields (status -> activity, state, health)
        migrations.RunPython(fix_fields_forwards, fix_fields_reverse),
    ]
