#!/usr/bin/env python3

##
# Copyright 2019 Mentor Graphics
# SPDX-License-Identifier: Apache-2.0


# import the basic python packages we need
import os
import sys
import tempfile
import pprint
import traceback
import json
import getpass
import getopt
import time
import subprocess
import tanrest

def git_revision_hash():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'])

loglevel=0

def usage():
    print("""
    Usage:
        get_sensor.py [options]
    
    Description:
        Gets a tanium sensor by name and writes it to a file
    
    Options:
        -h, --help      display this help and exit
        -s, --sensor    [required] name of the tanium sensor to get
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)

    Example:
        ./get_sensor_commit.py --server 139.181.111.21 --username tanium --sensor 'Chuck Norris Fact'

    """)


def main(argv):
    #print(argv)
    global loglevel
    creds = {}

    try:
        opts, args = getopt.getopt(argv,"d:hs:p:q:",["debug:","help","sensor=", "package=", "server=", "username=", "password="])
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
        if opt in ('--server'):
            creds['server'] = arg
        if opt in ('--username'):
            creds['username'] = arg
        if opt in ('--password'):
            creds['password'] = arg    

    try:
        sensorname
    except NameError:
        print("--sensor parameter required")
        usage()
        sys.exit(2)

    # create a dictionary of arguments for the pytan handler
    handler_args = {}

    if 'server' not in creds:
        print("--server parameter required")
        usage()
        sys.exit(2)
    else:
        if 'http' not in creds['server']:
            creds['server'] = 'https://' + creds['server']
        if '/api/v2' not in creds['server']:
            creds['server'] = creds['server'] + '/api/v2'

    if 'username' not in creds:
        creds['username'] = getpass.getuser()
    if 'password' not in creds:
        creds['password'] = getpass.getpass()

    tan = tanrest.server(creds)

    #print(tan.get_session())

    sensor = tan.get_sensor(sensorname)

    if not sensor:
        print('error getting sensor')
        sys.exit(3)
    
    for descriptionline in sensor["description"].splitlines():
        if descriptionline.startswith("commit="):
            print(descriptionline.split("=")[1])

if __name__ == "__main__":
   main(sys.argv[1:])
