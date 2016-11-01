# Copyright (c) 2011-2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from nova.scheduler import filters
from oslo_log import log as logging
from nova.scheduler.filters import utils

LOG = logging.getLogger(__name__)
SLA = 'sla'


class SlaFilter(filters.BaseHostFilter):
    """Filters Hosts by sla key.

    Works with aggregate metadata sla:key,
    where the key is customized.
    """

    # Availability zones do not change within a request
    run_filter_once_per_request = True

    def host_passes(self, host_state, spec_obj):
        instance_type = spec_obj.flavor
        if not instance_type.extra_specs:
            return True

        sla_key_found = 0
        metadata = utils.aggregate_metadata_get_by_host(
            host_state, key='availability_zone')
        LOG.debug("metadata: {0}".format(metadata))

        for key, req in instance_type.extra_specs.iteritems():
            scope = key.split(':')
            if scope[0] == SLA:
                sla_key_found = 1

            if len(scope) > 1 and scope[0] == SLA:
                if key in metadata and req in metadata[key]:
                    return True
            else:
                continue

        return False if sla_key_found else True