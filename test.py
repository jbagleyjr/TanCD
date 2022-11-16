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
        --persona       [optional] the persona to use for the session

    Example:
        python3 -i test.py --server 139.181.111.21 --username user123

    """)

argv = sys.argv[1:]
#print(argv)
global loglevel
creds = {}

try:
    opts, args = getopt.getopt(argv,"dhs:",["debug","help","server=", "username=", "password=", "persona="])
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
    if opt in ('--persona'):
        creds['persona'] = arg

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

question_info = tan.get_saved_question(118613)

print('original question text is: ' + question_info['query_text'])

print('url for original saved question is: https://tanium.wv.mentorg.com/#/interact/sq/118613')

modified_question = tan.parse_question(question_info['query_text'] + ' with DISW Division equals ICVS')

print('modified question text is: ' + question_info['query_text'] + ' with DISW Division equals ICVS')

modified_question_id = tan.ask_question(modified_question['data'][0])

print('url for modified question is: https://tanium.wv.mentorg.com/#/interact/q/' + str(modified_question_id))

