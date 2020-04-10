#!/usr/bin/env python3

##
# Copyright 2019 Mentor Graphics
# SPDX-License-Identifier: Apache-2.0

import json, time, sys, base64
from pprint import pprint as pp
from time import sleep
import getpass
import getopt
import tempfile
import ssl
import urllib.request

import subprocess

import configparser

config = configparser.ConfigParser()
config.readfp(open('content.cfg'))

def usage():
    print("""
    Usage:
        check_package.py [options]
    
    Description:
        Check's a package against defined standards in content.cfg.
    
    Options:
        -h, --help      display this help and exit
        -p, --package   [required] name of the tanium package to get
        -d, --debug     turn on debugging

    Example:
        ./check_sensor.py --package 'Puppet Apply Linux'

    """)

def main(argv):
    #print(argv)
    global loglevel
    creds = {}

    try:
        opts, args = getopt.getopt(argv,"d:h:p",["debug:","help","package="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        if opt in ('-s', '--package'):
            packagename = arg
        if opt in ('d', '--debug'):
            loglevel = arg

    try:
        packagename
    except NameError:
        print("--package parameter required")
        usage()
        sys.exit(2)

    ##
	# load the JSON object.
    with open('package/'+packagename+'.json') as json_data:
        package = json.load(json_data)
        json_data.close()

    failmessage="Package '" + package["name"] + "' failed testing!"
    failurecount=0

    warnmessage="Package '" + package["name"] + "' has warnings:"
    warncount=0


    if "files" in package:
        for file in package["files"]:
            if 'source' not in file:
                failmessage+="\n\nPackage files must be remote files, not local files."
                failurecount+=1
            else:
                if file["download_seconds"] > int(config.get('package','max_download_seconds')):
                    failmessage+="\n\nFile (" + file["name"] + ") exceeds max download seconds."
                    failmessage+="\n Set 'Check for update' to " + config.get('package', 'max_download_seconds') + " seconds or less."
                    failurecount+=1
                try:
                    context = ssl._create_unverified_context()
                    response = urllib.request.urlopen(file["source"], context=context)
                    data = response.read()
                except:
                    failmessage+="\n\nFile source (" + file["source"] + ") is not downloadable."
                    failurecount+=1

                badurl=True
                for url in config.get('package','remote_file_urls').split(" "):
                    if url in file["source"]:
                        badurl=False
                if badurl:
                    failmessage+="\n\nRemote file url (" + file["source"] + ") is not allowed.\n Remote files must be hosted at one of these locations:"
                    failmessage+="\n   - " + "\n   - ".join(config.get('package','remote_file_urls').split(" "))


    if not package["name"].startswith(config.get('prefix','name')):
        if not package["name"].startswith(config.get('prefix','warn_name')):
            failmessage+="\n\nTo avoid confusion betwen Siemens DISW developed content and Tanium provided content, please prefix the name with '"
            failmessage+=config.get('prefix','name') + "'"
            failurecount+=1
        else:
            warnmessage+="\n  deprecated name prefix '" + config.get('prefix','warn_name') + "' should be updated to '" + config.get('prefix', 'name') + "'"
            warncount+=1


    if failurecount != 0:
        print(failmessage)
        sys.exit(failurecount)

    if warncount != 0:
        f = open('check_package_warnings.log', 'a')
        f.write(warnmessage + "\n\n")
        f.close()

if __name__ == "__main__":
   main(sys.argv[1:])