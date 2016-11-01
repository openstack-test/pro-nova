import os
import sys
import random

def mountGluster(clientList, dest):
    length = len(clientList)
    if length <= 0:
        print "no client host, can't mount glusterfs"
        return
    clientId = random.randint(0, length-1)
    print "mount client ip is %s"%clientList[clientId][:-1]
    mountString = "mount -t glusterfs "+ clientList[clientId][:-1]  + " " + dest
    print mountString
    res = os.popen(mountString)
    print res.read()
    chownShell = "chown nova:nova " + dest
    chmodShell = "chmod 777 " + dest
    os.system(chownShell)
    os.system(chmodShell)

if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        clientList = f.readlines()
    mountGluster(clientList, sys.argv[2])
