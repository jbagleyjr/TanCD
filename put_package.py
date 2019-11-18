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
        put_package.py [options]
    
    Description:
        Takes a package file and uploads it to a Tanium server with the following changes:
            - Force setting the process group flag
            - tagging with current git commit hash
    
    Options:
        -h, --help      display this help and exit
        -p, --package   [required] name of the tanium package to put
        --server        [required] tanium server (ip address or dns name) [required]
        --branch        update file URLs to use specific branch
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)

    Example:
        ./put_package.py --server 139.181.111.21 --username tanium --package 'MGC Puppet Apply Linux'

    """)

def main(argv):
    #print(argv)
    global loglevel
    creds = {}

    try:
        opts, args = getopt.getopt(argv,"d:hs:p:q:b:",["debug:","help","sensor=", "package=", "branch=", "server=", "username=", "password="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    branch = False

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        if opt in ('-p', '--package'):
            packagename = arg
        if opt in ('-b', '--branch'):
            branch = arg
        if opt in ('d', '--debug'):
            loglevel = arg
        if opt in ('--server'):
            creds['server'] = arg
        if opt in ('--username'):
            creds['username'] = arg
        if opt in ('--password'):
            creds['password'] = arg    

    try:
        packagename
    except NameError:
        print("--package parameter required")
        usage()
        sys.exit(2)

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

    #print(tan.get_session())

    ##
	# load the JSON and make some additions to it before sending to tanium.
    with open('package/'+packagename+'.json') as json_data:
        package = json.load(json_data)
        json_data.close()

    if not package:
        print('error getting sensor')
        sys.exit(3)

    tan = tanrest.server(creds)

    tan.quiet = True
    package_id = tan.get_package_id(packagename)
    tan.quiet = False
    

    i=0
    for file in package["files"]:
        if 'commit=' in file["name"]:
            del package["files"][i]
        elif branch:
            if "https://itgitlab.wv.mentorg.com/Tanium/tanium-content/raw/" in file["source"]:
                filearray=file["source"].split("/")
                filearray[6]=branch
                package["files"][i]["source"]="/".join(filearray)
        i=i+1

        commithashtag = {
            '_type': 'file',
            'name': "commit="+git_revision_hash(),
            'download_seconds': 3600,
            'source': 'https://itgitlab.wv.mentorg.com/Tanium/tanium-content/raw/master/package_files/empty.txt'
        }

    ##
    # Force setting the process group flag.
    package["process_group_flag"]=1
    #content["package_spec"][0]["process_group_flag"]=1

    if package_id:
        if tan.update_package(package_id, package):
            print('updated existing package: ' + package["name"] + ' (' + str(package_id) + ')')

    else:
        resp = tan.create_package(package)
        if resp:
            print('created new package: ' + package["name"] + ' (' + str(resp['data']['id']) + ')')


if __name__ == "__main__":
   main(sys.argv[1:])

