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
import os
import tanrest
import subprocess

config = tanrest.config()

failcount=0
warncount=0

analyze = {
    'UnixShell': {
        'command': '/usr/bin/shellcheck',
        'arguments': config.get('package','shellcheck_params') + ' <%file>',
        'hashbang': 'sh',
        'suffix': '.sh'
    },
    'Powershell': {
        'command': 'powershell.exe -command',
        'arguments': "Invoke-ScriptAnalyzer -Path <%file>",
        'hashbang': False,
        'suffix': '.ps1'
    },
    'Python': {
        'command': '/usr/bin/pylint',
        'arguments': '<%file>',
        'hashbang': 'python',
        'suffix': '.py'
    }
}

def usage():
    print("""
    Usage:
        analyze.py [options]
    
    Description:
        Runs static analysis against tanium sensor content.
    
    Options:
        -h, --help      display this help and exit
        -t, --type      [required] the type of script
        -d, --debug     turn on debugging

    """)

def fail(sensor,script,output):
    global failcount
    if failcount==0:
        print("\n" + sensor["name"] + ' (' + script["platform"] + " - " + script["script_type"] + ') has failed static analysis.')
    
    print(" > " + output)
    failcount+=1

def warning(sensor,script,output):
    global warncount
    f = open("analyze_sensor_" + script["script_type"] + "_warnings.log", "a")
    f.write("\n" + sensor["name"] + ' (' + script["platform"] + " - " + script["script_type"] + ") has warnings.\n")
    f.write(output)
    f.close
    warncount+=1

def main(argv):
    global failcount
    global warncount
    try:
        opts, args = getopt.getopt(argv,"d:ht:",["debug:","help","type="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        if opt in ('-t', '--type'):
            script_type = arg
        if opt in ('d', '--debug'):
            loglevel = arg

    if not os.path.exists("updated_sensors.txt"):
        print('no sensor updates to analyze (missing updated_sensor.txt).')
        sys.exit(0)

    with open ("updated_sensors.txt", "r") as updated_sensors:
        sensornames=updated_sensors.readlines()

    ##
    # load the JSON object.
    for sensorname in sensornames:
        with open('sensor/' + sensorname.strip() + '.json') as json_data:
            sensor = json.load(json_data)
            json_data.close()
        
        #pp(sensor)

        for script in sensor["queries"]:
            #pp(script)
            if script["script_type"] == script_type:
                if script_type not in analyze:
                    output = "WARNING: No static analysis available for " + script_type
                    warning(sensor,script,output)
                    continue

                output=""

                f = tempfile.NamedTemporaryFile(mode='w',delete=False,suffix=analyze[script_type]["suffix"])
                f.write(script["script"])
                f.flush()
                f.close()

                if analyze[script_type]["hashbang"]:
                    if analyze[script_type]["hashbang"] not in script["script"].split("\n")[0]:
                        fail(sensor,script,'Bad hashbang for ' + script_type + ': ' + script["script"].split("\n")[0] + "\n")

                command = analyze[script_type]["command"] + " " + analyze[script_type]["arguments"]
                command = command.replace('<%file>', f.name)

                analysis = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if script_type == 'UnixShell':
                    if analysis.wait() != 0:
                        os.remove(f.name)
                        fail(sensor,script,output + "\n" + analysis.communicate()[0].decode())
                elif script_type == 'Powershell':
                    analysis.wait()
                    output = analysis.communicate()[0].decode()
                    os.remove(f.name)
                    if 'Error' in output:
                        fail(sensor,script,output)
                    if 'Warning' in output:
                        warning(sensor,script,output)
                elif script_type == 'Python':
                    analysis.wait()
                    output+=analysis.communicate()[0].decode()
                    if '\nE' in output or '\nF' in output:
                        fail(sensor,script,output)
                    if '\nW' in output or '\nC' in output or '\nR' in output:
                        warning(sensor,script,output)
                else:
                    output = "WARNING: No static analysis available for " + script_type
                    warning(sensor,script,output)
                        
            
    if failcount > 0:
        sys.exit(failcount)
 
if __name__ == "__main__":
   main(sys.argv[1:])

if failcount > 0:
    sys.exit(1)
