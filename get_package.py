#!/usr/bin/env python3

##
# Copyright 2019 Mentor Graphics
# SPDX-License-Identifier: Apache-2.0

import tanrest, json, time, sys, base64, os
from pprint import pprint as pp
from time import sleep
from requests import get
import getpass
import getopt

def usage():
    print("""
    Usage:
        get_package.py [options]
    
    Description:
        Gets a tanium package by name and writes it to a file
    
    Options:
        -h, --help      display this help and exit
        -p, --package   [required] name of the tanium package to get
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)
        --persona       [optional] the persona to use for the session

    Example:
        ./get_package.py --server 139.181.111.21 --username tanium --package 'MGC Puppet Apply Linux'

    """)

def download(url, file_name):
    # open in binary mode
    with open(file_name, "wb") as file:
        # get request
        response = get(url, verify=False)
        # write to file
        file.write(response.content)

def main(argv):
    #print(argv)
    global loglevel
    creds = {}

    try:
        opts, args = getopt.getopt(argv,"d:hs:p:q:",["debug:","help","sensor=", "package=", "server=", "username=", "password=", "persona="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        if opt in ('-p', '--package'):
            packagename = arg
        if opt in ('d', '--debug'):
            loglevel = arg
        if opt in ('--server'):
            creds['server'] = arg
        if opt in ('--username'):
            creds['username'] = arg
        if opt in ('--password'):
            creds['password'] = arg
        if opt in ('--persona'):
            creds['persona'] = arg

    try:
        packagename
    except NameError:
        print("--package parameter required")
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
        
        server = creds['server'].split('/')[2]

    if 'username' not in creds:
        creds['username'] = getpass.getuser()
    if 'password' not in creds:
        creds['password'] = getpass.getpass()

    tan = tanrest.server(creds)

    package = tan.get_package(packagename)

    downloadfiles=False
    if 'files' in package:
        for packagefile in package['files']:
            if not packagefile['source'].startswith('https'):
                print('need to download package file')
                pp(packagefile)
                downloadfiles=True

# https://tanium-test.wv.mentorg.com/cache/f45a5f9f5bfaaf9b23d2605d2767aae72f7167de2037cce95473d9ab1bdd0975
    if downloadfiles:
        if not os.path.exists('package/' + packagename):
            os.mkdir('package/' + packagename)

        packagefiles = tan.get_package_file_details(packagename)
        # pp(packagefiles)
        for packagefile in packagefiles:
            print('downloading file...')
            print('https://' + server + '/cache/' + packagefile['hash'])
            print(packagename + "/" + packagefile['name'])
            download('https://' + server + '/cache/' + packagefile['hash'], 'package/' + packagename + "/" + packagefile['name'])

    # pp(package)
    if not package:
        print('error getting package')
        sys.exit(3)

    out = json.dumps(package, indent=4)
    f = open('package/'+packagename+'.json', 'w')
    f.write(out)
    f.close()

    print('wrote ' + str( out.__sizeof__() ) + ' bytes to "package/' + packagename + '.json"')

    #qid = tan.req('get', 'saved_questions/by-name/Running%20Applications')['data']['id']
    #print tan.ask(qid)

if __name__ == "__main__":
   main(sys.argv[1:])

