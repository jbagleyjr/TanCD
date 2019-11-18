#!/bin/bash +x

echo -n "taniumuser: "
echo "$taniumuser"
echo
echo

git log --name-status -1 | grep "^A\|^M" | grep "sensor/" | awk -F/ '{ print $2 }' | awk -F. '{ print $1 }' > updated_sensors.txt
git log --name-status -1 | grep "^A\|^M" | grep "package/" | awk -F/ '{ print $2 }' | awk -F. '{ print $1 }' > updated_packages.txt
git log --name-status -1 | grep "^A\|^M" | grep "package_files/" | awk -F/ '{ print $(NF-1)"/"$NF }' > updated_package_files.txt

sensors=()
packages=()

exitval=0

while read -r line
do
    echo "testing sensor - <$line>"
    ./test_sensor.py --server tanium-test.wv.mentorg.com --sensor "$line" --username "$taniumuser" --password "$taniumpass"
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
    echo "testing package - <$line>"
    ./test_package.py --server tanium-test.wv.mentorg.com --package "$line" --username "$taniumuser" --password "$taniumpass"
    if [ $? -eq 0 ]
    then
    	packages+=($line)
    else
    	exitval=$((exitval+1))
    fi
done < "updated_packages.txt"


sensorsstring=$(printf ",'%s'" "${sensors[@]}")
sensorsstring=${sensorsstring:1}
packagesstring=$(printf ",'%s'" "${packages[@]}")
packagesstring=${packagesstring:1}

echo "sensors=$sensorsstring"
echo "packages=$packagesstring"

exit $exitval
