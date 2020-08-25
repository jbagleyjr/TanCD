#!/usr/bin/env python3

##
# Copyright 2019 Mentor Graphics
# SPDX-License-Identifier: Apache-2.0

import tanrest, json, time, sys, base64,subprocess
from pprint import pprint as pp
from time import sleep
import getpass
import getopt
import re


import configparser

config = configparser.ConfigParser()
config.readfp(open('content.cfg'))

def git_revision_hash():
    return subprocess.getoutput('git rev-parse --short HEAD')

def usage():
    print("""
    Usage:
        deploy_python.py [options]
    
    Description:
        Deploys TanCD bundled python content (uploaded with put_python.py) to all Tanium endpoints
        that need it.  This uses the 'TanCD Python Update Needed' sensor so it can be re-run fairly
        frequently without much overhead.

    Options:
        -h, --help      display this help and exit
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)

    Example:
        ./deploy_python.py --server 139.181.111.21 --username tanium

    """)

def escape_ansi(line):
	ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
	try:
		return ansi_escape.sub('', line)
	except:
		return 'no output'

def main(argv):
    #print(argv)
    global loglevel
    creds = {}

    try:
        opts, args = getopt.getopt(argv,"d:hs:p:q:",["debug:","help","server=", "username=", "password="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        if opt in ('d', '--debug'):
            loglevel = arg
        if opt in ('--server'):
            creds['server'] = arg
        if opt in ('--username'):
            creds['username'] = arg
        if opt in ('--password'):
            creds['password'] = arg    

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

    action_spec = {
        "name" : "Deploy TanCD Python Content",
        "package_spec" : {
            "source_id" : tan.get_package_id('TanCD Python Content'),
            "parameters": []
        },
        "action_group" : {
            "id" : tan.get_action_group_id("all computers")
        },
       "target_group" : {
            'and_flag': True,
            'filters': [
                {
                    'sensor': {
                        'source_hash': tan.get_sensor_hash("TanCD Python Update Needed"),
                        'parameters': [
                            {
                                "key": "||commit||",
                                "value": str(git_revision_hash())
                            }
                        ],
                    },
                    'operator': 'Equal',
                    'value': 'True',
                    'value_type': 'String',
                    'ignore_case_flag': True,
                }				
            ]           
       },
        "expire_seconds" : 900
    }

    action = tan.run_action(action_spec,get_results = True)

    pp(action)

if __name__ == "__main__":
   main(sys.argv[1:])

