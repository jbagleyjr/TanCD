#!/bin/bash +x

sensors=()
packages=()

while read -r line
do
    echo "pushing updated sensor - <$line>"
    TanCD/put_sensor.py --sensor "$line" --server "$1" --username "$taniumuser" --password "$taniumpass"
    if [ $? -eq 0 ]
    then
    	sensors+=($line)
    else
    	exitval=$((exitval+1))
    fi   	
done < "updated_sensors.txt"

##
# pickup changes to package files and associate to package.
while read -r line
do
	packagename="$(egrep "$line" package/* | awk -F\/ '{ print $2 }' | awk -F. '{ print $1 }')"
    if [ "$(grep -c "$line" updated_packages.txt)" -eq 0 ]
    then 
    	echo "$packagename" >> updated_packages.txt
    fi
done < "updated_package_files.txt"

while read -r line
do
    echo "pushing updated package - <$line>"
    TanCD/put_package.py --package "$line" --server "$1" --username "$taniumuser" --password "$taniumpass"
    if [ $? -eq 0 ]
    then
    	packages+=($line)
    else
    	exitval++
    fi
done < "updated_packages.txt"

sensorsstring=$(printf ",'%s'" "${sensors[@]}")
sensorsstring=${sensorsstring:1}
packagesstring=$(printf ",'%s'" "${packages[@]}")
packagesstring=${packagesstring:1}

echo "sensors=$sensorsstring"
echo "packages=$packagesstring"

