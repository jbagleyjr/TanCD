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
        put_sensor.py [options]
    
    Description:
        Takes a sensor file and uploads it to a Tanium server with the following changes:
            - adding default platform scripts from content.cfg
            - tagging with current git commit hash
    
    Options:
        -h, --help      display this help and exit
        -s, --sensor    [required] name of the tanium sensor to get
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)

    Example:
        ./put_sensor.py --server 139.181.111.21 --username tanium --sensor 'Chuck Norris Fact'

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
    with open('sensor/'+sensorname+'.json') as json_data:
        sensor = json.load(json_data)
        json_data.close()

    if not sensor:
        print('error getting sensor')
        sys.exit(3)

    tan = tanrest.server(creds)

    tan.quiet = True
    sensor_id = tan.get_sensor_id(sensorname)
    tan.quiet = False
    
    ##
    # map of what platform script type to use to auto-add "NA on platform" responses.
    platforms = {'Windows': 'VBScript','Linux': 'UnixShell', 'Mac': 'UnixShell', 'Solaris': 'UnixShell', 'AIX': 'UnixShell'}

    for platform in platforms:
        platformscript = [script for script in sensor["queries"] if script['platform'] == platform ]
        ##
        # if a script for platform is not in the sensor add the "NA on platform" response.

        if len(platformscript) == 0:
            print("Adding default " + platform + " script.")
            defaultscript = {
                'platform': platform,
                'script_type': platforms[platform],
                'script': config.get('platform_default_sensors', platform)
			}
            sensor["queries"].append(defaultscript)

    description = ""
    for descriptionline in sensor["description"].splitlines():
        if not descriptionline.startswith("commit="):
            description+=descriptionline + "\n"

    description+="commit="+str(git_revision_hash())

    sensor["description"]=description

    if sensor_id:
        if tan.update_sensor(sensor_id, sensor):
            print('updated existing sensor: ' + sensor["name"] + ' (' + str(sensor_id) + ')')

    else:
        resp = tan.create_sensor(sensor)
        if resp:
            print('created new sensor: ' + sensor["name"] + ' (' + str(resp['data']['id']) + ')')


if __name__ == "__main__":
   main(sys.argv[1:])

