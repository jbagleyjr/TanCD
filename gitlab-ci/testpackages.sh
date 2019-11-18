#!/bin/bash +x

echo -n "taniumuser: "
echo "$taniumuser"
echo
echo

packages=()

exitval=0

while read -r line
do
    echo "testing package - <$line>"
    TanCD/test_package.py --server tanium-test.wv.mentorg.com --package "$line" --username "$taniumuser" --password "$taniumpass"
    if [ $? -eq 0 ]
    then
    	packages+=($line)
    else
    	exitval=$((exitval+1))
    fi
done < "updated_packages.txt"

packagesstring=$(printf ",'%s'" "${packages[@]}")
packagesstring=${packagesstring:1}

echo "sensors=$sensorsstring"
echo "packages=$packagesstring"

exit $exitval

