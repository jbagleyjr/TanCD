#!/usr/bin/env python3

##
# Copyright 2019 Mentor Graphics
# SPDX-License-Identifier: Apache-2.0

import tanrest, json, time, sys, base64
from pprint import pprint as pp
from time import sleep
import getpass
import getopt
import re


import configparser

config = configparser.ConfigParser()
config.readfp(open('content.cfg'))

def usage():
    print("""
    Usage:
        test_package.py [options]
    
    Description:
        Tests a package - measures performance and execution
    
    Options:
        -h, --help      display this help and exit
        -s, --package    [required] name of the tanium package to test
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)

    Example:
        ./test_package.py --server 139.181.111.21 --username tanium --package 'MGC Puppet Check Linux'

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
        opts, args = getopt.getopt(argv,"d:hs:p:q:",["debug:","help","sensor=", "package=", "server=", "username=", "password="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        if opt in ('-s', '--package'):
            packagename = arg
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
    package = tan.get_package(packagename)

    failmessage="Package '" + packagename + "' failed testing!"
    failurecount=0

    #tan.quiet = True
    #qid = tan.ask_question(question)
    if package["command"][0:4] == "/bin":
        action_group = "all linux"
    elif package["command"][0:3] == "cmd":
        action_group = "all windows"
    elif "linux" in packagename.lower():
        action_group = "all linux"
    elif "windows" in packagename.lower():
        action_group = "all windows"
    else:
        action_group = "All Computers"
        # failmessage+="\n\n\nUnable to determine action group (Windows|Linux) to execute package on."
        # failurecount+=1

    #pp(package)

    parameter_definition = json.loads(package["parameter_definition"])
    action_spec = {
        "name" : "test_package.py " + packagename,
        "package_spec" : {
            "source_id" : tan.get_package_id(packagename),
            "parameters": []
        },
        "action_group" : { 
            "id" : tan.get_action_group_id(action_group)
        },
        "target_group" : {
            'and_flag': True,
            'filters': [
                {
                    'sensor': {
                        'source_hash': tan.get_sensor_hash("Online")
                    },
                    'operator': 'Equal',
                    'value': 'True',
                    'value_type': 'String',
                    'ignore_case_flag': True,
                }
            ]
        },
        "expire_seconds" : package["expire_seconds"]
    }

    parameter_definition = json.loads(package["parameter_definition"])
    #pp(parameter_definition)
    for parameter in parameter_definition["parameters"]:
        if not parameter["defaultValue"]:
            failmessage+="\n\nNo default value provided for package input parameter: " + parameter["key"]
            failurecount+=1
        else:
            pp(parameter)
            addparam = {
                "key" : parameter["key"],
                "value" : parameter["defaultValue"]
            }
            #pp(addparam)
            action_spec["package_spec"]["parameters"].append(addparam)
            #action_spec["parameters"].append(addparam)

    #addparam = {
    #    "key": "$1",
    #    "value": "mytagvalue"
    #}

    #action_spec["package_spec"]["parameters"].append(addparam)
    #pp(action_spec)
    #sys.exit(0)
    #action = tan.req('POST', 'actions/', action_spec)
    action = tan.run_action(action_spec,get_results = True)
    #pp(action["action_id"])

    #sys.exit(0)

    packageoutput="<h2>" + packagename + " output:</h2> \n"

    # Get MGC Tanium Action Output[75490] from all machines
    outputquestion = {
        "selects": [
            {
                "sensor": {
                    "name": "MGC Tanium Action Output",
                    "source_hash": tan.get_sensor_hash("MGC Tanium Action Output"),
                    "parameters": [
                        {
                            "key": "||actionNumber||",
                            "value": str(action["action_id"])
                        }
                    ]
                }
            }
        ]
    }

    performancequestion = {
        "selects": [
            {
                "sensor": {
                    "name": "MGC Package Performance",
                    "source_hash": tan.get_sensor_hash("MGC Package Performance"),
                    "parameters": [
                        {
                            "key": "||actionid||",
                            "value": str(action["action_id"])
                        }
                    ]
                }
            }
        ]
    }
    
    #tan.debug=True
    tan.question_complete_percent=1.00
    pqid = tan.ask_question(performancequestion)
    oqid = tan.ask_question(outputquestion)
    performance = tan.get_question_results(pqid)
    outputs = tan.get_question_results(oqid)

    summary_performance_results = {}
    summary_performance_results["count"] = 0
    summary_performance_results["exit_code"] = 0
    summary_performance_results["totruntime"] = 0
    summary_performance_results["maxruntime"] = 0

    pp(' - action output - ')
    pp(outputs)
    pp(' - /action output - ')

    actionout = {}
    for output in outputs["result_sets"]:
        for row in output["rows"]:
            key=row["data"][0][0]["text"]
            linenum=row["data"][1][0]["text"]
            text=row["data"][2][0]["text"]
            #pp("key: " + key)
            #pp("linenum: " + linenum)
            #pp("text: " + text)
            try:
                #out[key][linenum]=text
                if key in actionout:
                    actionout[key][linenum] = text
                else:
                    actionout[key] = {
                        linenum: text
                    }
            except:
                print("unable to parse record.")
                print(row)

    print("action output data")
    pp(actionout)

    for md5 in actionout:
        logs = [None] * 5
        for logentry in actionout[md5]:
            for index in logentry:
                print(md5 + " log index " + index)
                if md5 == "[no results]":
                    continue
                #print(escape_ansi(actionout[md5][index]))
                #logs[int(index)]=escape_ansi(actionout[md5][index])
                try:
                    logs[int(index)]=escape_ansi(actionout[md5][index])
                except:
                    print("error adding logentry to message.")
        
        packageoutput += '<ul>'
        for log in logs:
            if log != None:
                packageoutput += '<li>' + log + '</li>'
        packageoutput += '</ul>'


    for result in performance["result_sets"]:
        for row in result["rows"]:
            try:
                summary_performance_results["exit_code"]+=int(row["data"][3][0]["text"])
                summary_performance_results["totruntime"]+=float(row["data"][2][0]["text"])
                if summary_performance_results["maxruntime"] < float(row["data"][2][0]["text"]):
                    summary_performance_results["maxruntime"]=float(row["data"][2][0]["text"])
                summary_performance_results["count"]+=int(row["data"][4][0]["text"])
            except:
                print("unable to parse record.")

    if summary_performance_results["count"] == 0:
        failmessage+="\n\n\nUnable to collect performance data for " + packagename
        failurecount+=1
    else:
        summary_performance_results["avgruntime"]=float(summary_performance_results["totruntime"]) / float(summary_performance_results["count"])

        htmloutput="<h2>" + packagename + " performance:</h2>\n"
        htmloutput+="<ul>\n"
        htmloutput+="<li>average runtime: " + str(summary_performance_results["avgruntime"]) + " seconds</li>\n"
        htmloutput+="<li>max runtime: " + str(summary_performance_results["maxruntime"]) + " seconds</li>\n"
        htmloutput+="<li>exit code: " + str(summary_performance_results["exit_code"]) + "</li>\n"
        htmloutput+="</ul>"

        if summary_performance_results["avgruntime"] > config.getint('package','warn_avgruntime'):
            htmloutput+="<h3>WARNING: package '" + packagename + "' has an average runtime longer than " + str(config.getint('package', 'warn_avgruntime')) + "</h3>"

        if summary_performance_results["maxruntime"] > config.getint('package','warn_maxruntime'):
            htmloutput+="<h3>WARNING: package '" + packagename + "' has a max runtime longer than " + str(config.getint('package','warn_maxruntime')) + "</h3>"

        htmloutput+=packageoutput

        if summary_performance_results["exit_code"] > 0:
            failmessage+="\n\n\nDetected non-zero exit code."
            failurecount+=1

        if summary_performance_results["avgruntime"] > config.getint('package','fail_avgruntime'):
            failmessage+="\n\n\nPackage average runtime is too long (" + int(summary_performance_results["avgruntime"]) + ")"
            failmessage+="\nMax allowed average runtime is: " + str(config.getint('package','fail_avgruntime'))
            failurecount+=1

        #fail_maxruntime
        if summary_performance_results["maxruntime"] > config.getint('package','fail_maxruntime'):
            failmessage+="\n\n\nPackage max runtime is too long (" + int(summary_performance_results["maxruntime"]) + ")"
            failmessage+="\nMax allowed runtime is: " + str(config.getint('package','fail_maxruntime'))
            failurecount+=1

    if failurecount != 0:
        print(failmessage)
        sys.exit(failurecount)
    else:
        f = open('test_package_summary.html', 'a')
        f.write(htmloutput)
        f.close()

    #pp(performance)

if __name__ == "__main__":
   main(sys.argv[1:])

