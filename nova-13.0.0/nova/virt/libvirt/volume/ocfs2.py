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


from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging
import six

from nova.i18n import _LE, _LW
from nova import paths
from nova import utils
from nova.virt.libvirt import utils as libvirt_utils
from nova.virt.libvirt.volume import fs

CONF = cfg.CONF
CONF.import_opt('qemu_allowed_storage_drivers',
                'nova.virt.libvirt.volume.volume',
                group='libvirt')

volume_opts = [
    cfg.StrOpt('ocfs2_mount_point_base',
               default="/var/lib/cinder/ocfs2-volumes",
               help='Directory where the OCFS2 volume is mounted on the'
                    'compute node'),
    ]

CONF.register_opts(volume_opts, 'libvirt')

LOG = logging.getLogger(__name__)


class LibvirtOcfs2VolumeDriver(fs.LibvirtBaseFileSystemVolumeDriver):
    """Class implements libvirt part of volume driver for OCFS2."""

    def _get_mount_point_base(self):
        return CONF.libvirt.ocfs2_mount_point_base

    def get_config(self, connection_info, disk_info):
        """Returns xml for libvirt."""
        conf = super(LibvirtOcfs2VolumeDriver,
                     self).get_config(connection_info, disk_info)

        path = os.path.join(CONF.libvirt.ocfs2_mount_point_base, \
                            connection_info['data']['name'])
        conf.source_type = 'file'
        conf.source_path = path
        conf.driver_format = connection_info['data'].get('format', 'raw')
        return conf

    def connect_volume(self, connection_info, disk_info):
        """Connect the volume. Returns xml for libvirt."""
        options = connection_info['data'].get('options')
        self._ensure_mounted(connection_info['data']['export'], options)

        return self.get_config(connection_info, disk_info)

    def disconnect_volume(self, connection_info, disk_dev):
        """Disconnect the volume."""
        pass

    def _ensure_mounted(self, ocfs2_export, options=None):
        """@type nfs_export: string
           @type options: string
        """
        LOG.info("#"*80)
        LOG.info(ocfs2_export)
        LOG.info("#"*80)
        
        mount_path = CONF.libvirt.ocfs2_mount_point_base
        if not os.path.isdir(mount_path):
            msg = _LW("Cannot find ocfs2 share dir, check configuration")
            LOG.warn(msg)
            raise exception.NovaException(msg)
