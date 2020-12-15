#!/usr/bin/env python3

##
# Copyright 2019 Mentor Graphics
# SPDX-License-Identifier: Apache-2.0

import tanrest, json, time, sys, base64
from pprint import pprint as pp
from time import sleep
import getpass
import getopt

import configparser

config = configparser.ConfigParser()
config.readfp(open('content.cfg'))

def usage():
    print("""
    Usage:
        test_sensor.py [options]
    
    Description:
        Tests a sensor - measures performance and execution
    
    Options:
        -h, --help      display this help and exit
        -s, --sensor    [required] name of the tanium sensor to get
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)

    Example:
        ./test_sensor.py --server 139.181.111.21 --username tanium --sensor 'Chuck Norris Fact'

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

    #tan.quiet = True
    #qid = tan.ask_question(question)

    failmessage="Sensor '" + sensorname + "' failed testing!"
    failurecount=0

    sensoroutput="<h2>" + sensorname + " output:</h2> \n"

    print('Running sensor ' + sensorname + ' on ' + creds['server'])
    ##
    # run sensor 7 times - chosen by fair dice role
    for x in range(0, 7):
        qid = tan.run_sensors(sensorname)
        data = tan.get_question_results(qid)
        #pp(data["result_sets"])

        if x == 1:
            sensoroutput+="<table><tr>\n "
            for result in data["result_sets"]:
                for columnheader in result["columns"]:
                    sensoroutput+="<th>" + columnheader["name"] + "</th>"
                sensoroutput+="</tr>\n"
                for row in result["rows"]:
                    sensoroutput+="<tr>\n "
                    for column in row["data"]:
                        pp(column)
                        sensoroutput+="<td>" + column[0]["text"] + "</td>"
                    sensoroutput+="\n</tr>\n"
            sensoroutput+="\n</table>\n<br>\n\n"

    print('\nDone running sensor (' + sensorname + '), collecting performance data.\n')

    performancequestion = {
        #"query_text" : "get sensor performance[" + sensorname + "] from all machines",
        
        "selects": [
            {
                "sensor": {
                    "name": "TanCD Sensor Performance",
                    "source_hash": tan.get_sensor_hash("TanCD Sensor Performance"),
                    "parameters": [
                        {
                            "key": "||sensor||",
                            "value": sensorname
                        }
                    ]
                }
            }
        ]
    }

    qid = tan.ask_question(performancequestion)
    performance = tan.get_question_results(qid)

    #sensoroutput+="<h2>" + sensorname + " performance:</h2> \n"

    #sensoroutput+=tan.make_results_html(performance)

    summary_performance_results = {}
    summary_performance_results["count"] = 0
    summary_performance_results["exit_code"] = 0
    summary_performance_results["totruntime"] = 0
    summary_performance_results["maxruntime"] = 0

    for result in performance["result_sets"]:
        for row in result["rows"]:
            try:
                summary_performance_results["exit_code"]+=int(row["data"][7][0]["text"])
                summary_performance_results["totruntime"]+=float(row["data"][2][0]["text"])
                if summary_performance_results["maxruntime"] < float(row["data"][2][0]["text"]):
                    summary_performance_results["maxruntime"]=float(row["data"][2][0]["text"])
                summary_performance_results["count"]+=int(row["data"][8][0]["text"])
            except:
                print("unable to parse record.")

    print("summary_performance_results:\n")
    print(summary_performance_results)
    print("\n\n")

    if summary_performance_results["count"] == 0:
        failmessage+="\n\n\nUnable to collect performance data for " + sensorname
        failmessage+="\nPossibly the sensor_name variable does not match the sensor name?"
        failurecount+=1
    else:
        summary_performance_results["avgruntime"]=float(summary_performance_results["totruntime"]) / float(summary_performance_results["count"])

        htmloutput="<h2>" + sensorname + " performance:</h2>"
        htmloutput+="<ul>\n"
        htmloutput+="<li>average runtime: " + str(summary_performance_results["avgruntime"]) + " seconds</li>\n"
        htmloutput+="<li>max runtime: " + str(summary_performance_results["maxruntime"]) + " seconds</li>\n"
        htmloutput+="<li>exit code: " + str(summary_performance_results["exit_code"]) + "</li>\n"
        htmloutput+="</ul>"

        if summary_performance_results["avgruntime"] > config.getint('sensor','warn_avgruntime'):
            htmloutput+="<h3>WARNING: sensor '" + sensorname + "' has an average runtime longer than " + str(config.getint('sensor', 'warn_avgruntime')) + "</h3>"

        if summary_performance_results["maxruntime"] > config.getint('sensor','warn_maxruntime'):
            htmloutput+="<h3>WARNING: sensor '" + sensorname + "' has a max runtime longer than " + str(config.getint('sensor','warn_maxruntime'))

        htmloutput+=sensoroutput

        if summary_performance_results["exit_code"] > 0:
            failmessage+="\n\n\nDetected non-zero exit code."
            failurecount+=1

        if summary_performance_results["avgruntime"] > config.getint('sensor','fail_avgruntime'):
            failmessage+="\n\n\nSensor average runtime is too long (" + str(int(summary_performance_results["avgruntime"])) + ")"
            failmessage+="\nMax allowed average runtime is: " + str(config.getint('sensor','fail_avgruntime'))
            failurecount+=1

        #fail_maxruntime
        if summary_performance_results["maxruntime"] > config.getint('sensor','fail_maxruntime'):
            failmessage+="\n\n\nSensor max runtime is too long (" + str(int(summary_performance_results["maxruntime"])) + ")"
            failmessage+="\nMax allowed runtime is: " + str(config.getint('sensor','fail_maxruntime'))
            failurecount+=1

    if failurecount != 0:
        print(failmessage)
        sys.exit(failurecount)
    else:
        f = open('test_sensor_summary.html', 'a')
        f.write(htmloutput)
        f.close()

    print("\nCompleted testing.\n\n")

    pp(summary_performance_results)

if __name__ == "__main__":
   main(sys.argv[1:])

