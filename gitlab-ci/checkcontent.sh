#!/bin/bash +x

git log --name-status -1 | grep "^A\|^M" | grep "sensor/" | awk -F/ '{ print $2 }' | awk -F. '{ print $1 }' > updated_sensors.txt
git log --name-status -1 | grep "^A\|^M" | grep "package/" | awk -F/ '{ print $2 }' | awk -F. '{ print $1 }' > updated_packages.txt
git log --name-status -1 | grep "^A\|^M" | grep "package_files/" | awk -F/ '{ print $(NF-1)"/"$NF }' > updated_package_files.txt
git log --name-status -1 | grep "^A\|^M" | grep "py/" | awk -F/ '{ print $2 }' | awk -F. '{ print $1 }' > updated_python.txt

##
# if the updated_python.txt file size is greater than zero
if [ -s updated_python.txt ]
then
    echo "Checking if updated python content is used in any sensors or packages"
    while read -r line
    do
        echo "Checking for use of python module <$line>"
        modulename="$(echo $line | awk -F. '{ print $1 }')"
        egrep "$modulename" sensor/*.json | grep json | awk -F. '{ print $1 }' | awk -F\/ '{ print $2 }' | sort | uniq >> updated_sensors.txt
        egrep -r "$modulename" package_files | awk -F/ '{ print $(NF-1)"/"$NF }' | sort | uniq >> updated_package_files.txt
    done < updated_python.txt
fi

sensors=()
packages=()

exitval=0

##
# set locale to use UTF-8 to avoid this error from shellcheck
#	hGetContents: invalid argument (invalid byte sequence)
# reference: https://github.com/koalaman/shellcheck/issues/1277
export LC_ALL=en_US.UTF-8

#locale

while read -r line
do
    echo "testing sensor - <$line>"
    TanCD/check_sensor.py --sensor "$line"
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
    TanCD/check_package.py --package "$line"
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
