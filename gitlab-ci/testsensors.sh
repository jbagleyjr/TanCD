#!/bin/bash +x

echo -n "taniumuser: "
echo "$taniumuser"
echo
echo

sensors=()

exitval=0

while read -r line
do
    echo "testing sensor - <$line>"
    TanCD/test_sensor.py --server tanium-test.wv.mentorg.com --sensor "$line" --username "$taniumuser" --password "$taniumpass"
    if [ $? -eq 0 ]
    then
    	sensors+=($line)
    else
    	exitval=$((exitval+1))
    fi   	
done < "updated_sensors.txt"


sensorsstring=$(printf ",'%s'" "${sensors[@]}")
sensorsstring=${sensorsstring:1}

echo "sensors=$sensorsstring"

exit $exitval

