# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from stackdio.core.mixins import ParentRelatedMixin
from stackdio.core.permissions import StackdioPermissionsPermissions
from . import models


class FormulaRelatedMixin(ParentRelatedMixin):
    parent_queryset = models.Formula.objects.all()

    def get_formula(self):
        return self.get_parent_object()


class FormulaPermissionsMixin(FormulaRelatedMixin):
    permission_classes = (StackdioPermissionsPermissions,)

    def get_permissioned_object(self):
        return self.get_parent_object()
