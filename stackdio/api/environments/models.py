# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import unicode_literals

import logging
import os

import six
import yaml
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django_extensions.db.models import TimeStampedModel

from stackdio.api.formulas.models import FormulaVersion
from stackdio.core.constants import ComponentStatus, Health
from stackdio.core.fields import JSONField
from stackdio.core.utils import recursive_update

logger = logging.getLogger(__name__)


_environment_model_permissions = (
    'create',
    'admin',
)

_environment_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


@six.python_2_unicode_compatible
class Environment(TimeStampedModel):

    model_permissions = _environment_model_permissions
    object_permissions = _environment_object_permissions

    class Meta:
        ordering = ('name',)
        default_permissions = tuple(set(_environment_model_permissions +
                                        _environment_object_permissions))

    name = models.CharField('Name', max_length=255, unique=True)
    description = models.TextField('Description', blank=True, null=True)

    labels = GenericRelation('core.Label')

    formula_versions = GenericRelation('formulas.FormulaVersion')

    # The properties for this blueprint
    properties = JSONField('Properties')

    orchestrate_sls_path = models.CharField('Orchestrate SLS Path', max_length=255,
                                            default='orchestrate')

    def __str__(self):
        return six.text_type('Environment {}'.format(self.name))

    def get_root_directory(self):
        return os.path.join(settings.FILE_STORAGE_DIRECTORY,
                            'environments',
                            six.text_type(self.name))

    def get_log_directory(self):
        root_dir = self.get_root_directory()
        log_dir = os.path.join(root_dir, 'logs')
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        return log_dir

    def get_full_pillar(self):
        pillar_props = {}

        # If any of the formulas we're using have default pillar
        # data defined in its corresponding SPECFILE, we need to pull
        # that into our environment pillar file.

        # for each unique formula, pull the properties from the SPECFILE
        for formula_version in self.formula_versions.all():
            formula = formula_version.formula
            version = formula_version.version

            # Update the formula
            formula.get_gitfs().update()

            # Add it to the rest of the pillar
            recursive_update(pillar_props, formula.properties(version))

        # Add in properties that were supplied via the blueprint and during
        # environment creation
        recursive_update(pillar_props, self.properties)

        return pillar_props


class ComponentMetadataQuerySet(models.QuerySet):

    def create(self, **kwargs):
        if 'health' not in kwargs:
            current_health = kwargs.pop('current_health', None)
            if 'status' in kwargs:
                kwargs['health'] = ComponentMetadata.HEALTH_MAP[kwargs['status']] \
                                   or current_health \
                                   or Health.UNKNOWN
        return super(ComponentMetadataQuerySet, self).create(**kwargs)


@six.python_2_unicode_compatible
class ComponentMetadata(TimeStampedModel):

    # Limited health map - since we don't know what the components are,
    # we can't know if they're queued / running.
    HEALTH_MAP = {
        ComponentStatus.SUCCEEDED: Health.HEALTHY,
        ComponentStatus.FAILED: Health.UNHEALTHY,
        ComponentStatus.CANCELLED: None,
    }

    STATUS_CHOICES = tuple((x, x) for x in set(HEALTH_MAP.keys()))
    HEALTH_CHOICES = tuple((x, x) for x in set(HEALTH_MAP.values()) if x is not None)

    # Fields
    sls_path = models.CharField('SLS Path', max_length=128)

    host = models.CharField('Host', max_length=256)

    environment = models.ForeignKey('Environment', related_name='component_metadatas')

    status = models.CharField('Status',
                              max_length=32,
                              choices=STATUS_CHOICES,
                              default=ComponentStatus.QUEUED)

    health = models.CharField('Health',
                              max_length=32,
                              choices=HEALTH_CHOICES,
                              default=Health.UNKNOWN)

    objects = ComponentMetadataQuerySet.as_manager()

    def __str__(self):
        return six.text_type('Component {} for environment {} - {} ({})'.format(
            self.sls_path,
            self.environment.name,
            self.status,
            self.health,
        ))

    def set_status(self, status):
        # Make sure it's a valid status
        assert status in self.HEALTH_MAP

        self.status = status

        # Set the health based on the new status
        new_health = self.HEALTH_MAP[status]

        if new_health is not None:
            self.health = new_health

        self.save()
