#!/usr/bin/env python3
import tanrest, json, time, sys, base64
from pprint import pprint as pp
from time import sleep
import getpass
import getopt
from datetime import datetime, timedelta, timezone
from dateutil import parser

def usage():
    print("""
    Usage:
        actionfailures.py [options]
    
    Description:
        Gets last xx hours of action failures
    
    Options:
        -h, --help      display this help and exit
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)
        --hours         number of hours to go back in history to look for action failures

    Example:
        ./actionfailures.py --server 139.181.111.21 --username tanium --hours 24

    """)

def main(argv):
    #print(argv)
    global loglevel
    creds = {}

    try:
        opts, args = getopt.getopt(argv,"d:ht:p:q:",["debug:","help", "hours=", "server=", "username=", "password="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        if opt in ('-t', '--hours'):
            hours = int(arg)
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

    actions = tan.req('GET', 'actions')
    #pp(len(actions["data"]))
    #pp(actions["data"][-7])

    count=0
    notifyactions = {}

    for action in actions["data"]:
        if 'status' not in action:
            continue
        if action['status'] == 'Closed':
            expiration_time = parser.parse(action["expiration_time"])
            start_time = parser.parse(action["start_time"])
            action["expiration_time"] = expiration_time
            action["start_time"] = start_time
            #expiration_time = datetime.strptime(action['expiration_time'], '%Y-%m-%dT%H:%M:%S')
            #
            #if action['id'] == 132967:

            #if action['name'] == "Patch - Distribute Patch Tools - Windows" and expiration_time > datetime.now(timezone.utc) - timedelta(hours=hours):
            if expiration_time > datetime.now(timezone.utc) - timedelta(hours=hours):
                notify = False
                count+=1

                print(str(action['id']) + ' "' + action['name'] + '" ' +  str(expiration_time) + ' ' + str(action['user']['name']), end ="...", flush=True)

                action['notify_messages'] = []
                action['server'] = creds['server']
                #pp(action)

                if 'name' not in action['package_spec']:
                    notify = True
                    action['notify_messages'].append("Deployment references a package that doesn't exist.  Scheduled action needs to be deleted and re-created.")
                else:                        
                    tan.quiet=False
                    tan.debug=True
                    action['results'] = tan.get_action_results(action['id'])
                    if action['results']['error_count'] > 0 or tan.get_action_failure(action['id']):
                        notify = True
                        action['output'] = {}
                        actionfailedoutput = tan.get_action_failed_output(action['id'])
                        action['output']['logs'] = actionfailedoutput['data']
                        ##
                        # this is only needed to get the query text of the question which retrieves log output from endpoints.
                        # since tanium now provides a clean way to do this in the action history, this isn't needed anymore.
                        #action['output']['info'] = tan.get_question_info(actionfailedoutput['qid'])
                        action['output']['computers'] = tan.get_action_failed_computers(action['id'])
                        action['notify_messages'].append("Action exited with error or timeout")
                
                if notify:
                    #notify_action_owner(action)
                    notifyKey = action['name'] + " - " + action['user']['name']
                    print("Fail")
                    if notifyKey in notifyactions:
                        notifyactions[notifyKey].append(action)
                    else:
                        notifyactions[notifyKey]=[action]
                else:
                    print("Pass")

                #pp(action['results']['error_count'])

    #pp(notifyactions)
    for action_name in notifyactions:
        print("action name '" + action_name + "' has " + str(len(notifyactions[action_name])) + " actions")
        #print(actions.length + )
        notifyaction={}
        notifyaction["name"]=notifyactions[action_name][0]["name"]
        notifyaction["user"]=notifyactions[action_name][0]["user"]
        notifyaction["server"]=notifyactions[action_name][0]["server"]
        notifyaction["package_spec"]=notifyactions[action_name][0]["package_spec"]
        notifyaction["comment"]=notifyactions[action_name][0]["comment"]
        notifyaction["notify_messages"]=[]
        notifyaction["actions"]=[]
        notifyaction["logs"]=[]
        notifyaction["computers"]=[]
        for action in notifyactions[action_name]:
            # id number, start time, end time, number of systems
            # action["id"], action["start_time"], action["expiration_time"], action["results"]["row_count_machines"]
            #print("notify actions loop iteration begin")
            #action = notifyactions[action_name][i]
            #print("action is: ")
            #pp(action)
            #print("action length is: ")
            #pp(str(len(action)))
            #print("action type is: ")
            #pp(type(action))
            if len(action) < 3:
                continue
            try:
                print("action id is: " + str(action["id"]))
            except:
                print("action object garbled? continuing")
                continue
            ##
            # errors: aciton["output"]["logs"]
            # computers: action["output"]["computers"]
            notifyaction["actions"].append({
                'id': action["id"],
                'start_time': action["start_time"],
                'expiration_time': action["expiration_time"],
                'num_computers': action["results"]["row_count_machines"]
            })
            for log in action["output"]["logs"]:
                if log not in notifyaction["logs"]:
                    notifyaction["logs"].append(log)
            for computer in action["output"]["computers"]:
                if computer not in notifyaction["computers"]:
                    notifyaction["computers"].append(computer)
            for notifymessage in action["notify_messages"]:
                if notifymessage not in notifyaction["notify_messages"]:
                    notifyaction["notify_messages"].append(notifymessage)

        #print("\n\nnotifyaction is: \n")
        #pp(notifyaction)
        notify_action_owner(notifyaction)

    print("processed " + str(count) + " actions from the last " + str(hours) + " hours.")

def notify_action_owner(actions):
    # Import smtplib for the actual sending function
    import smtplib

    # Import the email modules we'll need
    from email.mime.text import MIMEText

    #print
    #print "Notify action owner called"
    #print action
    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(action)
    try:
        email=ldap_lookup_email(actions['user']['name'])
    except:
        email="Tanium-Global_Admin@mentor.com"

    #print email
    #print("notify_action_owner action object:")
    #pp(action)

    #expiration_time = parser.parse(actions["expiration_time"])

    body = str('')
    #body = body.encode('utf-8')

    body += '<p><h2>Action Summary</h2><ul>'
    body += '<li>Tanium Server: https://' + str(actions['server'].split('/')[2]) + '/</li>'
    #body += "<li>Action ID: " + str(action['id']) + "</li>"
    body += '<li>Action Owner: ' + str(actions['user']['name']) + '</li>'
    body += '<li>Action Name: ' + str(actions['name']) + '</li>'
    body += '<li>Package Name: ' + str(actions['package_spec']['name']) + "</li>"
    #body += '<li>Closed: ' + str(expiration_time) + '</li>'
    #body += '<li>Target count: ' + str(action['details']['count']) + '</li>'
    body += '</ul>'
    body += '</p>'

    #server = 'https://tanium.wv.mentorg.com/api/v2'

    body += '<p><table>'
    body += '<tr><th>Action ID</th><th>start</th><th>end</th><th>num computers</th></tr>'
    for action in actions['actions']:
        body += '<tr><td>'
        # https://tanium.wv.mentorg.com/#/actions/status?action_ids=132117
        body += '<a href=https://' + str(actions['server'].split('/')[2]) + '/#/actions/status?action_ids=' + str(action['id']) + '>' + str(action['id']) + '</a>'
        body += '</td><td>'
        body += str(action["start_time"].ctime())
        body += '</td><td>'
        body += str(action["expiration_time"].ctime())
        body += '</td><td>'
        body += str(action["num_computers"])
    body += '</table></p>'

    body += '<p><h2>Action Errors</h2><ul>'
    for message in actions['notify_messages']:
        body += '<li>' + str(message) + '</li>'
    body += '</ul></p>'

    ##
    # commenting this out because it seems to be useless noise. Maybe
    # it will be useful one day when we have all the other errors fix.
    # But, for now, it's bad.
    #if action['details']['count'] > 0:
    #    body += '<p><h2>Failed Machine Statuses</h2>'
    #    body += '<table><tr><th>Computer Name</th><th>Status</th></tr>'
    #    for status in action['details']['failedhostdata']:
    #        body += '<tr><td>' + status['computer_name'] + '</td><td>' + status['action_status'] + '</td></tr>'
    #    body += '</table></p>'

    #     if len(action['output']['log']) > 0:
    
    body += '<p><h2>Command Output</h2>'
    #body += '<b> Asking Question: </b><i>' +  action['output']['info']['query_text'] + '</i><br>'
    body += '<ul>'

    for log in actions['logs']:
        if log != None:
            body += '<li>' + str(log) + '</li>'

    body += '</ul>'
    body += '</p>'

    body += '<p><h2>Computers with failures</h2>'
    body += '<table>'
    for computer in actions['computers']:
        body += '<tr><td>' + str(computer["name"]) + '</td><td>' + str(computer["os"]) + '</td></tr>'
    body += '</li>'
    body += '</p>'

    ## uncomment the following to include deubgging data in the email.
    # this is handy for debugging or developing this script.
    #body += '<p><h2>Debug Data</h2></p>'
    #body += '<pre>'
    #body += pprint.pformat(action)
    #body += '</pre>'

    #msg = MIMEText(body.encode('utf-8').strip(), 'html')

    print("message body type: " + str(type(body)))

    #try:
    #    body = body.decode('utf-8')
    #except (UnicodeDecodeError, AttributeError):
    #    pass

    msg = MIMEText(str(body), 'html')

    # me == the sender's email address
    # you == the recipient's email address

    msg['Subject'] = actions['name'] + ' Tanium Action Failures' + ' (' + str(action['id']) + ')'
    msg['From'] = 'tanium@' + actions['server'].split("/")[2]
    msg['To'] = str(email)
    #msg['To'] = "james_bagley@mentor.com"

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    #s = smtplib.SMTP('localhost')
    #s.quit()
    s = smtplib.SMTP()
    s.connect('localhost', '25')
    #s.ehlo()
    #s.sendmail('tanium@tanium.wv.mentorg.com', ['james_bagley@mentor.com'], msg)
    #s.sendmail('tanium@tanium.wv.mentorg.com', [email], msg.as_string())
    s.send_message(msg)
    s.quit()

    print("Sent failure notification to " + email)

    return None

##
# TODO: make this user ldap server and basedn from content.cfg
#
def ldap_lookup_email(username):
    if username == 'tansvcact':
        return "Tanium-Global_Admin@mentor.com"

    if username[0:5] == "admin":
        username = username[5:len(username)]

    #username = 'jbagley'
    #print('ldap_lookup_email: ' + username)

    import ldap

    l = ldap.initialize('ldap://ldap.wv.mentorg.com')
    try:
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s()
        valid = True
    except error:
        print(error)

    basedn = "dc=mgc,dc=mentorg,dc=com"
    searchFilter = "(&(cn=" + username + ")(mail=*))"
    searchAttribute = ["mail"]
    searchScope = ldap.SCOPE_SUBTREE
    try:    
        ldap_result_id = l.search(basedn, searchScope, searchFilter, searchAttribute)
        #pp(ldap_result_id)
        result_set = []
        while 1:
            result_type, result_data = l.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else:
                ## if you are expecting multiple results you can append them
                ## otherwise you can just wait until the initial result and break out
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
        #pp(result_set)
        email = result_set[0][0][1]['mail'][0]
    except e:
        pp(e)
        email = "Tanium-Global_Admin@mentor.com"
    l.unbind_s()
    return email.decode("utf-8")


if __name__ == "__main__":
   main(sys.argv[1:])
