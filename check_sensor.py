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
import re
import subprocess
import configparser

config = configparser.ConfigParser()
config.read_file(open('content.cfg'))

def usage():
    print("""
    Usage:
        check_sensor.py [options]
    
    Description:
        Check's a sensor against defined standards in content.cfg and runs static analysis on scripts.
    
    Options:
        -h, --help      display this help and exit
        -s, --sensor    [required] name of the tanium sensor to get
        -d, --debug     turn on debugging

    Example:
        ./check_sensor.py --sensor 'Chuck Norris Fact'

    """)

def valid_chars(string):
    characherRegex = re.compile(r'[^a-zA-Z0-9\ \-]')
    string = characherRegex.search(string)
    return not bool(string)

def invalid_words(string):
    words = [
        'get',
        'and',
        'from',
        'machines',
        'with',
        'equal',
        'contain',
        'contains',
        'matches'
    ]
    invalid = []
    for word in words:
        if word in string.lower().split(" "):
            invalid.append(word)

    if len(invalid) == 0:
        return False
    else:
        return invalid

def main(argv):
    #print(argv)
    global loglevel
    creds = {}

    try:
        opts, args = getopt.getopt(argv,"d:h:s",["debug:","help","sensor="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        if opt in ('-s', '--sensor'):
            sensorname = arg
        if opt in ('d', '--debug'):
            loglevel = arg

    try:
        sensorname
    except NameError:
        print("--sensor parameter required")
        usage()
        sys.exit(2)

    ##
	# load the JSON object.
    with open('sensor/'+sensorname+'.json') as json_data:
        sensor = json.load(json_data)
        json_data.close()

    failmessage="Sensor '" + sensor["name"] + "' failed testing!"
    failurecount=0

    warnmessage="\n\nSensor '" + sensor["name"] + "' has warnings"
    warncount=0

    if not valid_chars(sensor["name"]):
        failmessage+="\n\nSensor name contains invalid characters.  Only alphanumeric, spaces and dashes are allowed."
        failurecount+=1

    if invalid_words(sensor["name"]):
        failmessage+="\n\nSensor name contains invalid words (" + ",".join(invalid_words(sensor["name"])) + ")."
        failurecount+=1

    #config.getint('sensor','minimum_max_age')
    if config.getint('sensor','minimum_max_age') > sensor["max_age_seconds"]:
        #failmessage+=content["sensor"][0]["name"] + " failed testing!"
        failmessage+="\n\nYou must set the 'Max Age' to be more than " + config.get('sensor','minimum_max_age') + " seconds."
        failurecount+=1
    
    prefixtest=False
    for prefix in config.get('prefix','category').split(","):
        if sensor["category"].startswith(prefix):
            prefixtest=True
    
    if not prefixtest:
        failmessage+="\n\nTo avoid confusion betwen Siemens DISW developed content and Tanium provided content, please prefix the content category with '"
        failmessage+=config.get('sensor','category_prefix') + "'"
        failurecount+=1

    prefixtest=False
    for prefix in config.get('prefix','name').split(","):
        if sensor["name"].startswith(prefix):
            prefixtest=True

    if not prefixtest:
        failmessage+="\n\nTo avoid confusion betwen Siemens DISW developed content and Tanium provided content, please prefix the name with '"
        failmessage+=config.get('prefix','name') + "'"
        failurecount+=1

    for script in sensor["queries"]:
        #print script["script"]
        if script["script_type"] == "UnixShell":

            if config.get('sensor','lnxperfinclude') not in script["script"]:
                if script["script"].strip() != config.get('platform_default_sensors', script["platform"]).strip():
                    failmessage+="\n\nUnixShell (" + script["platform"] + "):  All sensor scripts need to include the following lines near the top of the script for performance testing."
                    failmessage+="\n   export sensor_name=\"" + sensor["name"] + "\""
                    failmessage+="\n   " + config.get('sensor','lnxperfinclude')
                    failurecount+=1

        if script["script_type"] == "Powershell":

            if config.get('sensor','pshperfinclude') not in script["script"]:
                if script["script"].strip() != config.get('platform_default_sensors', script["platform"]).strip():
                    failmessage+="\n\nPowershell:  All sensor scripts need to include the following lines near the top of the script for performance testing."
                    failmessage+="\n   $sensor_name=\"" + sensor["name"] + "\""
                    failmessage+="\n   " + config.get('sensor','pshperfinclude')
                    failurecount+=1

    if failurecount != 0:
        print(failmessage)
        sys.exit(failurecount)

    if warncount != 0:
        f = open('check_sensor_warnings.log', 'a')
        f.write(warnmessage)
        f.close()

if __name__ == "__main__":
   main(sys.argv[1:])
