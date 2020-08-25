#!/usr/bin/env python3
import tanrest, json, time, sys, base64, os
from pprint import pprint as pp
from time import sleep
import getpass
import getopt

import subprocess

import configparser

config = configparser.ConfigParser()
config.readfp(open('content.cfg'))

def usage():
    print("""
    Usage:
        put_python.py [options]
    
    Description:
        Uploads python deployment package to the Tanium server.
        
        Files:
            - TanCD-python-windows.zip
            - TanCD-python-linux.zip
            - TanCD-python-install.py
        Command:
            $TANIUM_CLIENT_EXECUTABLE runscript InternalPython TanCD-python-install.py
    
    Options:
        -h, --help      display this help and exit
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)

    Example:
        ./put_python.py --server 139.181.111.21 --username tanium

    """)

def main(argv):

    global loglevel
    creds = {}

    try:
        opts, args = getopt.getopt(argv,"d:hs:p:q:b:",["debug:","help", "server=", "username=", "password="])
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
    #tan.debug = True

    files = []
    # Upload a base64 encoded file, capture the hash for future reference.
    for filepath in [ 'TanCD/package_files/TanCD-python-install.py', 'TanCD-python-linux.zip', 'TanCD-python-windows.zip' ]:
    #for filepath in [ 'TanCD/package_files/TanCD-python-install.py' ]:
        with open(filepath, 'rb') as fd:
            file_b64data = base64.b64encode(fd.read()).decode('ascii')
 
        file_data = {
            'bytes': file_b64data,
            'file_size': os.stat(filepath).st_size,
            'force_overwrite': 1
            #'start_pos': 0,
            #'part_size': os.stat(filepath).st_size
        }

        ##
        # TODO: handling chunking and sending file parts if the files get too large.

        file_obj = tan.req('POST', 'upload_file', data=file_data)
        pp(file_obj)

        file_hash = file_obj['data']['upload_file']['hash']

        sleep(1)
        file_status = tan.req('GET', 'upload_file/' + str(file_obj['data']['upload_file']['id']))

        pp(file_status['data']['upload_file_status']['file_cached'])

        files.append({
                'name': filepath.split('/')[-1],
                'hash': file_hash
            }
        )

    #all_package_files = tan.req('GET', 'package_files')
    #pp(all_package_files)
    #pp(results)
    package = {
        'name': 'TanCD Python Content',
        'display-name':'TanCD Python Content',
        'command': '$TANIUM_CLIENT_EXECUTABLE runscript InternalPython TanCD-python-install.py',
        'files': files,
        'expire_seconds': 900,
        "skip_lock_flag": False,
        "process_group_flag": True,
    }

    #pp(package)
    package_id = tan.get_package_id(package['name'])

    if package_id:
        if tan.update_package(package_id, package):
            print('updated existing package: ' + package["name"] + ' (' + str(package_id) + ')')
    else:
        resp = tan.create_package(package)
        if resp:
            print('created new package: ' + package["name"] + ' (' + str(resp['data']['id']) + ')')

if __name__ == "__main__":
   main(sys.argv[1:])
