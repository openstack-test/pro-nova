# Copyright (c) 2011 OpenStack Foundation
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

"""
The FilterScheduler is for creating instances locally.
You can customize this scheduler by specifying your own Host Filters and
Weighing Functions.
"""

import random

from oslo_log import log as logging
from six.moves import range

import nova.conf
from nova import exception
from nova.i18n import _
from nova import rpc
from nova.scheduler import driver
from nova.scheduler import scheduler_options
from nova import image

SCHED_POLICY_MEMORY = 1
SCHED_POLICY_VCPU = 2
SCHED_POLICY_DISK = 3

CONF = nova.conf.CONF
LOG = logging.getLogger(__name__)


class FilterScheduler(driver.Scheduler):
    """Scheduler that can be used for filtering and weighing."""
    def __init__(self, *args, **kwargs):
        super(FilterScheduler, self).__init__(*args, **kwargs)
        self.options = scheduler_options.SchedulerOptions()
        self.notifier = rpc.get_notifier('scheduler')

    def select_destinations(self, context, spec_obj):
        """Selects a filtered set of hosts and nodes."""
        self.notifier.info(
            context, 'scheduler.select_destinations.start',
            dict(request_spec=spec_obj.to_legacy_request_spec_dict()))

        num_instances = spec_obj.num_instances
        selected_hosts = self._schedule(context, spec_obj)

        # Couldn't fulfill the request_spec
        if len(selected_hosts) < num_instances:
            # NOTE(Rui Chen): If multiple creates failed, set the updated time
            # of selected HostState to None so that these HostStates are
            # refreshed according to database in next schedule, and release
            # the resource consumed by instance in the process of selecting
            # host.
            for host in selected_hosts:
                host.obj.updated = None

            # Log the details but don't put those into the reason since
            # we don't want to give away too much information about our
            # actual environment.
            LOG.debug('There are %(hosts)d hosts available but '
                      '%(num_instances)d instances requested to build.',
                      {'hosts': len(selected_hosts),
                       'num_instances': num_instances})

            reason = _('There are not enough hosts available.')
            raise exception.NoValidHost(reason=reason)

        dests = [dict(host=host.obj.host, nodename=host.obj.nodename,
                      limits=host.obj.limits) for host in selected_hosts]

        self.notifier.info(
            context, 'scheduler.select_destinations.end',
            dict(request_spec=spec_obj.to_legacy_request_spec_dict()))
        return dests

    def _get_configuration_options(self):
        """Fetch options dictionary. Broken out for testing."""
        return self.options.get_configuration()

    @staticmethod
    def has_sched_policy(spec_obj):
        instance_type = spec_obj.flavor
        extra_specs = instance_type.extra_specs
        if not extra_specs:
            return False

        return True if extra_specs.get('sched:policy') else False

    def weight_by_free_res(self, weighed_objs, resource):
        """
        Re-sort host by value of resource
        Valid resource values are:
            1 -- memory
            2 -- cpu
            3 -- disk
        """
        if not weighed_objs:
            return []

        LOG.debug("resource type: {0}".format(resource))
        LOG.debug("Host's attributes: {0}".format(dir(weighed_objs[0].obj)))
        if int(resource) == SCHED_POLICY_MEMORY:
            return sorted(weighed_objs, key=lambda x: x.obj.free_ram_mb, reverse=True)
        elif int(resource) == SCHED_POLICY_VCPU:
            return sorted(weighed_objs, key=lambda x: (x.obj.vcpus_total - x.obj.vcpus_used), reverse=True)
        elif int(resource) == SCHED_POLICY_DISK:
            return sorted(weighed_objs, key=lambda x: x.obj.free_disk_mb, reverse=True)
        else:
            LOG.warn("Resource value %s is not supported." % resource)
            return weighed_objs

    @staticmethod
    def need_select_image(spec_obj):
        """
        There'll be 'template' key/value in instance metadata
        if image should be re-selected.
        """
        inst_meta = spec_obj.scheduler_hints
        LOG.info('spec_obj.scheduler_hints: {0}'.format(spec_obj.scheduler_hints))
        return True if inst_meta and inst_meta.get('template') else False

    def select_all_related_img(self, context, value):
        """
        Filter images as to the property 'image_template' of images.
        """
        target_images = []
        image_api = image.API()
        # images = image_api.get_all(context)
        for img_uuid in value:
            img = image_api.get(context, img_uuid)
            if img:
                target_images.append(img)

        return target_images

    def select_images(self, context, spec_obj):
        base_image = []
        hint = spec_obj.scheduler_hints
        LOG.info('hint: {0}'.format(hint))
        if hint and hint.get('image_template'):
            image_uuids = hint.get('image_template')[0].split(',')
            base_image = self.select_all_related_img(context, image_uuids)

        return base_image

    def remove_invalid_hosts(self, images, hosts):
        valid_host = []
        for host in hosts:
            for image in images:
                img_hy_type = image.get('properties', {}).get('hypervisor_type')
                host_hv_type = host.obj.hypervisor_type.lower()
                if host_hv_type == 'ironic':
                    host_hv_type = 'baremetal'
                if not img_hy_type or (img_hy_type and img_hy_type.lower() not in host_hv_type):
                    continue
                valid_host.append(host)
        LOG.debug('valid host: {0}'.format(valid_host))
        return valid_host

    def _schedule(self, context, spec_obj):
        """Returns a list of hosts that meet the required specs,
        ordered by their fitness.
        """
        elevated = context.elevated()

        config_options = self._get_configuration_options()

        # Find our local list of acceptable hosts by repeatedly
        # filtering and weighing our options. Each time we choose a
        # host, we virtually consume resources on it so subsequent
        # selections can adjust accordingly.

        # Note: remember, we are using an iterator here. So only
        # traverse this list once. This can bite you if the hosts
        # are being scanned in a filter or weighing function.
        hosts = self._get_all_host_states(elevated)

        selected_hosts = []
        num_instances = spec_obj.num_instances
        # NOTE(sbauza): Adding one field for any out-of-tree need
        spec_obj.config_options = config_options
        for num in range(num_instances):
            # Filter local hosts based on requirements ...
            hosts = self.host_manager.get_filtered_hosts(hosts,
                    spec_obj, index=num)
            if not hosts:
                # Can't get any more locally.
                break

            LOG.debug("Filtered %(hosts)s", {'hosts': hosts})

            weighed_hosts = self.host_manager.get_weighed_hosts(hosts,
                    spec_obj)

            if self.has_sched_policy(spec_obj):
                weighed_hosts = self.weight_by_free_res(weighed_hosts,
                                                        spec_obj.flavor.extra_specs['sched:policy'])

            # need to filter out hosts whose hypervisor type is different with images'
            if self.need_select_image(spec_obj):
                images = self.select_images(context, spec_obj)
                weighed_hosts = self.remove_invalid_hosts(images, weighed_hosts)
            LOG.debug("Weighed %(hosts)s", {'hosts': weighed_hosts})

            if weighed_hosts:
                scheduler_host_subset_size = max(1,
                                                 CONF.scheduler_host_subset_size)
                if scheduler_host_subset_size < len(weighed_hosts):
                    weighed_hosts = weighed_hosts[0:scheduler_host_subset_size]
                chosen_host = random.choice(weighed_hosts)

                LOG.debug("Selected host: %(host)s", {'host': chosen_host})
                selected_hosts.append(chosen_host)

                # Now consume the resources so the filter/weights
                # will change for the next instance.
                chosen_host.obj.consume_from_request(spec_obj)
                if spec_obj.instance_group is not None:
                    spec_obj.instance_group.hosts.append(chosen_host.obj.host)
                    # hosts has to be not part of the updates when saving
                    spec_obj.instance_group.obj_reset_changes(['hosts'])

        return selected_hosts

    def _get_all_host_states(self, context):
        """Template method, so a subclass can implement caching."""
        return self.host_manager.get_all_host_states(context)
