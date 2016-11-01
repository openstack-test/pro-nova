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


import nova.conf
from nova.scheduler import filters
from oslo_log import log as logging
from nova.scheduler.filters import utils


LOG = logging.getLogger(__name__)

CONF = nova.conf.CONF


class ResourcePoolFilter(filters.BaseHostFilter):
    """Filters Hosts by availability zone.
    Note: in theory a compute node can be part of multiple availability_zones
    """

    # Availability zones do not change within a request
    run_filter_once_per_request = True

    def host_passes(self, host_state, spec_obj):
        instance_type = spec_obj.flavor
        specs = instance_type.extra_specs
        availability_zone_list = specs.get('sched:res_pool', {})
        #LOG.debug("availability_zone_list: {0}".format(availability_zone_list))

        if availability_zone_list:
            if not isinstance(availability_zone_list, (list, tuple)):
                availability_zone_list = availability_zone_list.split(',')

            metadata = utils.aggregate_metadata_get_by_host(
                host_state, key='availability_zone')
            LOG.debug("metadata: {0}".format(metadata))
            if 'availability_zone' in metadata:
                return metadata['availability_zone'].intersection(set(availability_zone_list))
            else:
                return CONF.default_availability_zone in availability_zone_list

        return True
