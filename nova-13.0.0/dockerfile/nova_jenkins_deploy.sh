#!/bin/bash

# del deploy node for old nova image
ssh 172.16.71.229 "docker rmi -f autodeploy.com:4000/kollaglue/centos-binary-nova-compute:2.0.1"

sleep 2

# del allinone node for old nova docker
ssh 172.16.71.230 "docker stop nova_compute"
ssh 172.16.71.230 "docker rm -f nova_compute"

sleep 2

# del allinone node for old nova image
ssh 172.16.71.230 "docker rmi -f autodeploy.com:4000/kollaglue/centos-binary-nova-compute"

sleep 2

# deploy node for pull/push and set image tag
ssh 172.16.71.229 "docker pull 172.16.71.229:4000/kollaglue/centos-binary-nova-compute:2.0.1"
ssh 172.16.71.229 "docker tag 172.16.71.229:4000/kollaglue/centos-binary-nova-compute:2.0.1 autodeploy.com:4000/kollaglue/centos-binary-nova-compute:2.0.1"
ssh 172.16.71.229 "docker rmi -f 172.16.71.229:4000/kollaglue/centos-binary-nova-compute:2.0.1"
ssh 172.16.71.229 "docker push autodeploy.com:4000/kollaglue/centos-binary-nova-compute:2.0.1"

sleep 2

# start deploy allinone
ssh 172.16.71.229 kolla-ansible deploy -i /usr/share/kolla/ansible/inventory/multinode -t nova -vvvvv
