#!/bin/bash
checkout_branch_tag(){
    git clone git@172.16.71.236:iaas/pro-nova.git
    cd pro-nova && git checkout master
}

work_dir="/tmp/work`echo $RANDOM`"
mkdir -p $work_dir && cd $work_dir
checkout_branch_tag && cd nova-13.0.0
cp -f dockerfile/nova-compute/* $work_dir
tar -cvf nova.tar nova && mv nova.tar $work_dir/

cd $work_dir
if [ -f Dockerfile ] && [ -f extend_start.sh ] && [ -f nova.tar ];then
    docker build --tag=172.16.71.221:4000/kollaglue/centos-binary-nova-compute:$_docker_tag .
    if [ $? -eq 0 ];then
        docker push 172.16.71.221:4000/kollaglue/centos-binary-nova-compute:$_docker_tag
        docker rmi -f 172.16.71.221:4000/kollaglue/centos-binary-nova-compute:$_docker_tag
    else
        echo "docker build nova-compute failed"
        exit 1
    fi
else
    echo "File does not exist"
    exit 1
fi
