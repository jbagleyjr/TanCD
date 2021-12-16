#!/usr/bin/env python3
import tanrest, json, time, sys, base64
from pprint import pprint as pp
from time import sleep
import getpass
import getopt

import subprocess

import configparser

config = configparser.ConfigParser()
config.readfp(open('content.cfg'))

def git_revision_hash():
    return subprocess.getoutput('git rev-parse HEAD')

def usage():
    print("""
    Usage:
        test.py [options]
    
    Description:
        For debugging, sets up a tan object for interactive use.
    
    Options:
        -h, --help      display this help and exit
        -s --server     [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)

    Example:
        python3 -i test.py --server 139.181.111.21 --username user123

    """)

argv = sys.argv[1:]
#print(argv)
global loglevel
creds = {}

try:
    opts, args = getopt.getopt(argv,"dhs:",["debug","help","server=", "username=", "password="])
except getopt.GetoptError:
    usage()
    sys.exit(2)

debug = False

for opt, arg in opts:
    if opt in ('-h', '--help'):
        usage()
        sys.exit(2)
    if opt in ('-p', '--package'):
        packagename = arg
    if opt in ('-b', '--branch'):
        branch = arg
    if opt in ('-d', '--debug'):
        debug = True
    if opt in ('s', '--server'):
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

tan = tanrest.server(creds, quiet=False, debug=debug, keepcreds=False)

qid = 144122

info = tan.get_saved_question_results(qid)

vulnapps = {}
vulnhashes = []
vulnfiles = []

count = 0

for result in info["result_sets"]:
    for row in result["rows"]:
        try:
            result = json.loads(row['data'][3][0]['text'])
        except:
            continue

        fullpath = result['properties']['fullpath']
        thishash = result['properties']['md5']

        count = count + 1
        if thishash not in vulnapps.keys():
            vulnapps[thishash] = [fullpath]

        if fullpath not in vulnapps[thishash]:
            vulnapps[thishash].append(fullpath)
        
        if fullpath not in vulnfiles:
            vulnfiles.append(fullpath)

        if thishash not in vulnhashes:
            vulnhashes.append(thishash)
