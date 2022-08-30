#!/bin/bash

##
# Comply unit test to verify no network filesystem access on Linux.
# run as root.  Required to be run on a system with _some_ nfs mounts.
#
# This test should be run anytime new vulnerability or compliance content
# is imported.  It works by measuring network traffic to/from the NFS servers
# holding mounts so needs to be run on a relatively quiet system.  There
# is a chance for false positives of this test if there is other activity
# on the system using the NFS mounts during the comply scan.
#

if [ "null${1}" != "null" ]
then
    testids=$1
else
    for dir in /opt/Tanium/TaniumClient/extensions/comply/data/results/*
    do
        id="$(echo $dir | awk -F\- '{ print $NF}')"
        testids="$testids $id"
    done
fi

uuid="$(uuidgen)"

nfsmountedservers="$(mount -t nfs | awk -F: '{ print $1 }')"
nfsmountcount="$(mount -t nfs | wc -l)"

if [ $nfsmountcount -eq 0 ]
then
    echo "test host needs to have at least one NFS mount.  Fail."
    exit 1
fi

for nfs_server in $nfsmountedservers
do
    iptables -I OUTPUT -d $nfs_server -m comment --comment $uuid
    iptables -I INPUT -d $nfs_server -m comment --comment $uuid
done

#
# run the comply scan here
export TANIUM_CLIENT_ROOT=/opt/Tanium/TaniumClient
#for id in $(cat /opt/Tanium/TaniumClient/extensions/comply/current-intel-config.json | grep filename | awk -F\- '{ print $NF }' | awk -F. '{ print $1 }')

for id in $testids
do
    dir="$(ls -1d /opt/Tanium/TaniumClient/extensions/comply/data/results/*-$id)"
    name="$(echo $dir | awk -F\/ '{ print $NF}')"    
    echo "run assessment $name $id"
    # delete the previous results dir, this forces a full comply scan
    rm -rf $dir

    # zero out the traffic counters
    iptables -Z
    /bin/bash /opt/Tanium/TaniumClient/Tools/Comply/run-assessment.sh $id 1
    #echo "$name $id"
    sleep 5s
    while [ ! -f $dir/0-results.xml ]
    do
        echo -n "."
        sleep 1s
    done
    tail $dir/0-stdout.txt

    for inbytes in $(iptables -nxvL INPUT | grep $uuid | awk '{ print $2 }')
    do
        if [ "$inbytes" -ne 0 ]
        then
            exitcode=1
            echo 
            echo "test detected NFS traffic during comply scan $id.  Fail."
            echo
            break
        fi
    done

    for outbytes in $(iptables -nxvL OUTPUT | grep $uuid | awk '{ print $2 }')
    do
        if [ $outbytes -ne 0 ]
        then
            exitcode=1
            echo 
            echo "test detected NFS traffic during comply scan $id.  Fail."
            echo
            break
        fi
    done
done


if [ $nfsmountcount -lt "$(mount -t nfs | wc -l)" ]
then
    echo "number of NFS mounts increased during comply scan.  Fail."
    exitcode=1
fi

for nfs_server in $nfsmountedservers
do
    iptables -D OUTPUT -d $nfs_server -m comment --comment $uuid
    iptables -D INPUT -d $nfs_server -m comment --comment $uuid
done

exit $exitcode
