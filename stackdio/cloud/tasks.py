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


from celery import shared_task
from celery.utils.log import get_task_logger

from .models import CloudProvider


logger = get_task_logger(__name__)


@shared_task(name='cloud.get_provider_instances')
def get_provider_instances(provider_id):
    try:
        provider = CloudProvider.objects.get(id=provider_id)
        logger.info('CloudProvider: {0!r}'.format(provider))

    except CloudProvider.DoesNotExist:
        logger.error('Unknown CloudProvider with id {0}'.format(
            provider_id))
    except Exception, e:
        logger.exception('Unhandled exception retrieving instance sizes.')
