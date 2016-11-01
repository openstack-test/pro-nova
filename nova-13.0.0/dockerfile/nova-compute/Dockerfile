FROM autodeploy.com:4000/kollaglue/centos-binary-nova-base:2.0.1
MAINTAINER Kolla Project (https://launchpad.net/kolla)

RUN yum -y install \
        openstack-nova-compute \
        openvswitch \
        sysfsutils \
        ceph-common \
        genisoimage \
	glusterfs-fuse \
        iscsi-initiator-utils \
        targetcli \
    && yum clean all

COPY extend_start.sh /usr/local/bin/kolla_nova_extend_start
RUN chmod 755 /usr/local/bin/kolla_nova_extend_start \
    && rm -f /etc/machine-id \
    && mv /usr/lib/python2.7/site-packages/nova{,.bak}
ADD nova.tar /usr/lib/python2.7/site-packages

COPY initiatorname.iscsi /etc/iscsi/initiatorname.iscsi
COPY mountGlusterfs.py /home/
RUN chown nova:nova /home/mountGlusterfs.py &&\
    chmod 755 /home/mountGlusterfs.py

