# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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


import logging
import json
import os

import yaml
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django_extensions.db.models import (
    TimeStampedModel,
    TitleSlugDescriptionModel,
)

from stackdio.core.queryset_transform import TransformManager, TransformQuerySet
from stackdio.core.fields import DeletingFileField
from .utils import get_cloud_provider_choices, get_provider_type_and_class

logger = logging.getLogger(__name__)

FILESYSTEM_CHOICES = (
    ('ext2', 'ext2'),
    ('ext3', 'ext3'),
    ('ext4', 'ext4'),
    ('fuse', 'fuse'),
    ('xfs', 'xfs'),
)


def get_config_file_path(obj, filename):
    return obj.slug + '.conf'


def get_global_orch_props_file_path(obj, filename):
    return "cloud/{0}/global_orch.props".format(obj.slug)


_cloudprovider_model_permissions = ()
_cloudprovider_object_permissions = ('view', 'admin')


class CloudProvider(models.Model):

    model_permissions = _cloudprovider_model_permissions
    object_permissions = _cloudprovider_object_permissions

    class Meta:
        default_permissions = tuple(set(_cloudprovider_model_permissions +
                                        _cloudprovider_object_permissions))

    PROVIDER_CHOICES = get_cloud_provider_choices()
    name = models.CharField(
        'Name',
        max_length=32,
        choices=PROVIDER_CHOICES,
        unique=True)

    def __unicode__(self):
        return self.name


_cloudaccount_model_permissions = (
    'create',
    'admin',
)

_cloudaccount_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


class CloudAccount(TimeStampedModel, TitleSlugDescriptionModel):

    model_permissions = _cloudaccount_model_permissions
    object_permissions = _cloudaccount_object_permissions

    class Meta:
        unique_together = ('title', 'provider')
        ordering = ('provider', 'title')

        default_permissions = tuple(set(_cloudaccount_model_permissions +
                                        _cloudaccount_object_permissions))

    # What is the type of provider (e.g., AWS, Rackspace, etc)
    provider = models.ForeignKey('cloud.CloudProvider', verbose_name='Cloud Provider')

    # Used to store the provider-specifc YAML that will be written
    # to disk in settings.STACKDIO_CONFIG.salt_providers_dir
    yaml = models.TextField()

    # The region for this provider
    # FOR EC2 CLASSIC
    region = models.ForeignKey('CloudRegion', verbose_name='Region')

    # Are we using VPC?
    # FOR EC2 VPC
    vpc_id = models.CharField('VPC ID', max_length=64, blank=True)

    # the account/owner id of the account
    account_id = models.CharField('Account ID', max_length=64)

    formula_versions = GenericRelation('formulas.FormulaVersion')

    # salt-cloud provider configuration file
    config_file = DeletingFileField(
        max_length=255,
        upload_to=get_config_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(
            location=settings.STACKDIO_CONFIG.salt_providers_dir))

    # storage for properties file
    global_orch_props_file = DeletingFileField(
        max_length=255,
        upload_to=get_global_orch_props_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    def __unicode__(self):
        return self.title

    @property
    def vpc_enabled(self):
        return len(self.vpc_id) > 0

    def get_driver(self):
        # determine the type and implementation class for this account
        ptype, pclass = get_provider_type_and_class(self.provider.id)

        # instantiate the implementation class and return it
        return pclass(self)

    def update_config(self):
        """
        Writes the yaml configuration file for the given account object.
        """
        # update the account object's security group information
        security_groups = [sg.group_id for sg in self.security_groups.filter(
            is_default=True
        )]
        account_yaml = yaml.safe_load(self.yaml)
        account_yaml[self.slug]['securitygroupid'] = security_groups
        self.yaml = yaml.safe_dump(account_yaml, default_flow_style=False)
        self.save()

        if not self.config_file:
            self.config_file.save(self.slug + '.conf',
                                  ContentFile(self.yaml))
        else:
            with open(self.config_file.path, 'w') as f:
                # update the yaml to include updated security group information
                f.write(self.yaml)

    @property
    def global_orchestration_properties(self):
        if not self.global_orch_props_file:
            return {}
        with open(self.global_orch_props_file.path) as f:
            return json.loads(f.read())

    @global_orchestration_properties.setter
    def global_orchestration_properties(self, props):
        props_json = json.dumps(props, indent=4)
        if not self.global_orch_props_file:
            self.global_orch_props_file.save(
                get_global_orch_props_file_path(self, None),
                ContentFile(props_json))
        else:
            with open(self.global_orch_props_file.path, 'w') as f:
                f.write(props_json)

    def get_root_directory(self):
        return os.path.join(settings.FILE_STORAGE_DIRECTORY, 'cloud', self.slug)

    def get_formulas(self):
        formulas = set()
        for component in self.global_formula_components.all():
            formulas.add(component.component.formula)

        return list(formulas)


class CloudInstanceSize(TitleSlugDescriptionModel):
    class Meta:
        ordering = ('id',)

        default_permissions = ()

    # `title` field will be the type used by salt-cloud for the `size`
    # parameter in the providers yaml file (e.g., 'Micro Instance' or
    # '512MB Standard Instance'

    # link to the type of provider for this instance size
    provider = models.ForeignKey('cloud.CloudProvider', verbose_name='Cloud Provider')

    # The underlying size ID of the instance (e.g., t1.micro)
    instance_id = models.CharField('Instance ID', max_length=64)

    def __unicode__(self):
        return '{0} ({1})'.format(self.description, self.instance_id)


class GlobalOrchestrationFormulaComponent(TimeStampedModel):
    """
    An extension of an existing FormulaComponent to add additional metadata
    for those components based on this account. In particular, this is how
    we track the order in which the formula should be provisioned during
    global orchestration.
    """

    class Meta:
        verbose_name_plural = 'global orchestration formula components'
        ordering = ('order',)

        default_permissions = (
            'create',
            'view',
            'update',
            'delete',
        )

    # The formula component we're extending
    component = models.ForeignKey('formulas.FormulaComponent')

    # The cloud this extended formula component applies to
    account = models.ForeignKey('cloud.CloudAccount',
                                related_name='global_formula_components')

    # The order in which the component should be provisioned
    order = models.IntegerField(default=0)

    def __unicode__(self):
        return u'{0}:{1}'.format(
            self.component,
            self.account
        )


_cloudprofile_model_permissions = (
    'create',
    'admin',
)

_cloudprofile_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


class CloudProfile(TimeStampedModel, TitleSlugDescriptionModel):

    model_permissions = _cloudprofile_model_permissions
    object_permissions = _cloudprofile_object_permissions

    class Meta:
        unique_together = ('title', 'account')

        default_permissions = tuple(set(_cloudprofile_model_permissions +
                                        _cloudprofile_object_permissions))

    # What cloud account is this under?
    account = models.ForeignKey('cloud.CloudAccount', related_name='profiles')

    # The underlying image id of this profile (e.g., ami-38df83a')
    image_id = models.CharField('Image ID', max_length=64)

    # The default instance size of this profile, may be overridden
    # by the user at creation time
    default_instance_size = models.ForeignKey('CloudInstanceSize',
                                              verbose_name='Default Instance Size')

    # The SSH user that will have default access to the box. Salt-cloud
    # needs this to provision the box as a salt-minion and connect it
    # up to the salt-master automatically.
    ssh_user = models.CharField('SSH User', max_length=64)

    # salt-cloud profile configuration file
    config_file = DeletingFileField(
        max_length=255,
        upload_to=get_config_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(
            location=settings.STACKDIO_CONFIG.salt_profiles_dir
        )
    )

    def __unicode__(self):
        return self.title

    def update_config(self):
        """
        Writes the salt-cloud profile configuration file
        """
        profile_yaml = {
            self.slug: {
                'provider': self.account.slug,
                'image': self.image_id,
                'size': self.default_instance_size.title,
                'ssh_username': self.ssh_user,
                'script': settings.STACKDIO_CONFIG.get('salt_bootstrap_script',
                                                       'bootstrap-salt'),
                'script_args': settings.STACKDIO_CONFIG.get('salt_bootstrap_args',
                                                            ''),
                'sync_after_install': 'all',
                # PI-44: Need to add an empty minion config until salt-cloud/701
                # is fixed.
                'minion': {},
            }
        }
        profile_yaml = yaml.safe_dump(profile_yaml,
                                      default_flow_style=False)

        if not self.config_file:
            self.config_file.save(self.slug + '.conf',
                                  ContentFile(profile_yaml))
        else:
            with open(self.config_file.path, 'w') as f:
                # update the yaml to include updated security group information
                f.write(profile_yaml)

    def get_driver(self):
        return self.account.get_driver()


_snapshot_model_permissions = (
    'create',
    'admin',
)

_snapshot_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


class Snapshot(TimeStampedModel, TitleSlugDescriptionModel):

    model_permissions = _snapshot_model_permissions
    object_permissions = _snapshot_object_permissions

    class Meta:
        unique_together = ('snapshot_id', 'account')

        default_permissions = tuple(set(_snapshot_model_permissions +
                                        _snapshot_object_permissions))

    # The cloud account that has access to this snapshot
    account = models.ForeignKey('cloud.CloudAccount', related_name='snapshots')

    # The snapshot id. Must exist already, be preformatted, and available
    # to the associated cloud account
    snapshot_id = models.CharField(max_length=32)

    # How big the snapshot is...this doesn't actually affect the actual
    # volume size, but mainly a useful hint to the user
    size_in_gb = models.IntegerField()

    # the type of file system the volume uses
    filesystem_type = models.CharField(max_length=16,
                                       choices=FILESYSTEM_CHOICES)


class CloudRegion(TitleSlugDescriptionModel):
    class Meta:
        unique_together = ('title', 'provider')
        ordering = ('provider', 'title')

        default_permissions = ()

    # link to the type of provider for this zone
    provider = models.ForeignKey('cloud.CloudProvider', verbose_name='Cloud Provider')

    def __unicode__(self):
        return self.title


class CloudZone(TitleSlugDescriptionModel):
    class Meta:
        unique_together = ('title', 'region')
        ordering = ('region', 'title')

        default_permissions = ()

    # link to the region this AZ is in
    region = models.ForeignKey('CloudRegion', related_name='zones')

    def __unicode__(self):
        return self.title


class SecurityGroupQuerySet(TransformQuerySet):
    def with_rules(self):
        return self.transform(self._inject_rules)

    def _inject_rules(self, queryset):
        """
        Pull all the security group rules using the cloud account's
        implementation.
        """
        by_account = {}
        for group in queryset:
            by_account.setdefault(group.account, []).append(group)

        for account, groups in by_account.iteritems():
            group_ids = [group.group_id for group in groups]
            driver = account.get_driver()
            account_groups = driver.get_security_groups(group_ids)

            # add in the rules
            for group in groups:
                group.rules = account_groups[group.name]['rules']


class SecurityGroupManager(TransformManager):
    def get_queryset(self):
        return SecurityGroupQuerySet(self.model)


_securitygroup_model_permissions = (
    'create',
    'admin',
)

_securitygroup_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


class SecurityGroup(TimeStampedModel, models.Model):

    model_permissions = _securitygroup_model_permissions
    object_permissions = _securitygroup_object_permissions

    class Meta:
        unique_together = ('name', 'account')

        default_permissions = tuple(set(_securitygroup_model_permissions +
                                        _snapshot_object_permissions))

    objects = SecurityGroupManager()

    # Name of the security group (REQUIRED)
    name = models.CharField(max_length=255)

    # Description of the security group (REQUIRED)
    description = models.CharField(max_length=255)

    # ID given by the provider
    # NOTE: This will be set automatically after it has been created on the
    # account and will be ignored if passed in
    group_id = models.CharField(max_length=16, blank=True)

    # The stack that the security group is for (this is only
    # useful if it's a managed security group)
    stack = models.ForeignKey('stacks.Stack',
                              null=True,
                              related_name='security_groups')

    blueprint_host_definition = models.ForeignKey(
        'blueprints.BlueprintHostDefinition',
        null=True,
        default=None,
        related_name='security_groups')

    # the cloud account for this group
    account = models.ForeignKey('cloud.CloudAccount', related_name='security_groups')

    # ADMIN-ONLY: setting this to true will cause this security group
    # to be added automatically to all machines that get started in
    # the related cloud account
    is_default = models.BooleanField(default=False)

    # Flag for us to track which security groups were created by
    # stackd.io and should be managed by the system. Any stack
    # that is launched will have n security groups created and
    # managed, where n is the number of distinct host definitions
    # based on the blueprint used to create the stack
    is_managed = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def get_active_hosts(self):
        return self.hosts.count()

    def rules(self):
        """
        Pulls the security groups using the cloud provider
        """
        logger.debug('SecurityGroup::rules called...')
        driver = self.account.get_driver()
        try:
            groups = driver.get_security_groups([self.group_id])
            return groups[self.name]['rules']
        except KeyError:
            logger.debug(groups)
            raise