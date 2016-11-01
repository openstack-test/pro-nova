#!/bin/bash

echo "start build nova ..."
for pro_name in nova-compute
do
    _nova_path="/opt/pro-nova/nova-13.0.0/dockerfile"
    echo "${_nova_path}/${pro_name}/${pro_name}.sh"
    cd ${_nova_path}/${pro_name} && ./${pro_name}.sh
    sleep 2
    echo "#######################"
done

