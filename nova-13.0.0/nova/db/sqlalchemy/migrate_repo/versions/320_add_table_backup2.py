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

# This is a placeholder for Icehouse backports.
# Do not use this number for new Juno work.  New Juno work starts after
# all the placeholders.
#
# See blueprint backportable-db-migrations-juno
# http://lists.openstack.org/pipermail/openstack-dev/2013-March/006827.html


# add table backup2 for backup

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table

from oslo_utils import timeutils

def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    table = Table('backup2', meta,
            Column('created_at', DateTime, default=timeutils.utcnow),
            Column('updated_at', DateTime, onupdate=timeutils.utcnow),
            Column('deleted_at', DateTime),
            Column('deleted', Integer, default=0),
            Column('id', String(36), nullable=False, index=True, primary_key=True),
            Column('image_ref', String(255), nullable=True),
            Column('instance_uuid', String(255), nullable=True),
            Column('backup_time', String(255), nullable=True),
            Column('backup_path', String(255), nullable=True),
            Column('backup_size', String(255), nullable=True),
            Column('backup_status', String(255), nullable=True),
            Column('display_name', String(255), nullable=True),
            Column('display_description', String(255), nullable=True),
            mysql_engine='InnoDB',
            mysql_charset='utf8'
    )
    table.create()


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    table = Table('backup2', meta, autoload=True)
    table.drop()
