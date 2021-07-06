#!/usr/bin/env python

##
# Copyright 2019 Mentor Graphics
# SPDX-License-Identifier: Apache-2.0


from requests import Request, Session
from pprint import pprint as pp
import time, json, atexit, re
from datetime import datetime, timezone
from dateutil import parser
import configparser
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os

##
# just a standard way to read content.cfg
#   config class extends configparser with some pathing magic
class config(configparser.ConfigParser):
	def __init__(self, configfile = 'content.cfg'):
		super(config, self).__init__()
		self.configfilepath=self.get_config_abspath(configfile)
		self.read_config(self.configfilepath)

	def get_config_abspath(self, configfile):
		if os.name == 'nt':
			pathsep = "\\"
		else:
			pathsep = "/"

		patharr = os.path.dirname(os.path.abspath(__file__)).split(pathsep)
		filepath = pathsep.join(patharr[0:patharr.index("TanCD")]) + pathsep + configfile
		if os.path.exists(filepath):
			return filepath
		elif os.path.exists(pathsep.join(patharr) + pathsep + configfile):
			return pathsep.join(patharr) + pathsep + configfile

	def read_config(self, filepath):
		self.read(filepath)

##
# the actual tanrest class starts here
class server():
	def __init__(self, creds, debug = False, quiet=False):
		self.s = Session()
		self.debug = debug
		self.quiet = quiet
		self.question_complete_percent = 0.97
		self.action_complete_percent = 0.8
		self.creds = creds
		self.server = str(creds['server']) if creds['server'][-1] == '/' else str(creds['server'] + '/')
		self.get_session()
		atexit.register(self.logout)
		self.saved = [i['id'] for i in self.req('get', 'saved_questions')['data'] if 'id' in i]
		##
		# disable warnings after the first requests to ensure it gets displayed at least once 
		# before being supressed.
		requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	def get_session(self):
		r = Request('POST', self.server + 'session/login', json=self.creds).prepare()
		if self.debug:
			print(r.body)
		resp = self.s.send(r, verify=False)
		if self.debug:
			pp(vars(resp))
		self.session_id = (resp.json()['data']['session'])
		self.session_time = time.time()
		return True

	def logout(self):
		r = Request('POST', self.server + 'session/logout', json={'session': self.session_id}).prepare()
		if self.debug:
			print(r.body)
		resp = self.s.send(r, verify=False)
		if self.debug:
			pp(vars(resp))
		return True

	def validate_session(self):
		# Validate session, renew if expired, send request verbosely.
		if time.time() - self.session_time < 60:
			# if the session id is less than a minute old then assume it's still valid
			return True
		else:
			r = Request('POST', self.server + 'session/validate', json={'session':self.session_id}).prepare()
			valid = self.s.send(r, verify=False)
			if valid.status_code == 403:
				if not self.quiet:
					print('Session expired, renewing.')
				self.get_session()
			elif valid.status_code == 200:
				return True
			else:
				return False

	def get_package(self, packagename):
		package = self.req('GET', 'packages/by-name/' + packagename)
		if package:
			del package["data"]["id"]
			del package["data"]["available_time"]
			del package["data"]["creation_time"]
			del package["data"]["modification_time"]
			del package["data"]["last_update"]
			del package["data"]["last_modified_by"]
			if "files" in package["data"]:
				if self.debug:
					pp(package["data"]["files"])
				for file in package["data"]["files"]:
					try:
						del file["id"]
						del file["status"]
						del file["bytes_total"]
						del file["bytes_downloaded"]
						del file["last_download_progress_time"]
						del file["download_start_time"]
						del file["size"]
						del file["cache_status"]
						del file["file_status"]
						del file["hash"]
					except:
						continue
			return package["data"]
		else:
			return False

	def get_package_id(self, packagename):
		package = self.req('GET', 'packages/by-name/' + packagename)
		if package:
			return package["data"]["id"]
		else:
			return False

	def update_package(self, id, package):
		print('id is ' + str(id))
		return self.req('PATCH', 'packages/' + str(id), package)

	def create_package(self, package):
		return self.req('POST', 'packages/', package)
		
	def get_sensor(self, sensorname):
		#self.validate_session()
		#sensor = Request('GET', self.server + 'sensors/by-name/' + sensorname)
		sensor = self.req('GET', 'sensors/by-name/' + sensorname)
		if sensor:
			del sensor["data"]["id"]
			del sensor["data"]["hash"]
			del sensor["data"]["creation_time"]
			del sensor["data"]["modification_time"]
			del sensor["data"]["last_modified_by"]
			return sensor["data"]
		else:
			return False

	def get_sensor_hash(self, sensorname):
		sensor = self.req('GET', 'sensors/by-name/' + sensorname)
		if sensor:
			return sensor['data']['hash']
		else:
			##
			# this should throw an error and exit.
			return False

	def get_sensor_id(self, sensorname):
		#self.validate_session()
		#sensor = Request('GET', self.server + 'sensors/by-name/' + sensorname)
		sensor = self.req('GET', 'sensors/by-name/' + sensorname)
		#sensor = self.get_sensor(sensorname)
		if sensor:
			return sensor['data']['id']
		else:
			return False

	def update_sensor(self, id, sensor):
		# sensors/by-name/Chuck%20Norris%20Fact
		# /api/v2/sensors/{id}
		return self.req('PATCH', 'sensors/' + str(id), sensor)


	def create_sensor(self, sensor):
		# /api/v2/sensors
		return self.req('POST', 'sensors/', sensor)


	def req(self, type, endpoint, data={}):
		if type == 'PATCH':
			r = Request(type, self.server + endpoint, data=json.dumps(data), headers={'session':self.session_id}).prepare()			
		else:
			r = Request(type, self.server + endpoint, json=data, headers={'session':self.session_id}).prepare()
		if not self.validate_session():
			return False

		resp = self.s.send(r, verify=False)
		
		if resp.status_code == 200:
			return resp.json()
		else:
			if not self.quiet:
				print('Request error: ' + str(resp))
			if self.debug:
				pp('request object:')
				pp(vars(r))
				pp('response object:')
				pp(vars(resp))
			return False

	def get_action_group_id(self,action_group):
		return self.req('GET', 'action_groups/by-name/' + action_group)["data"]["id"]

	def get_scheduled_action_id(self,action_name):
		try:
			return self.req('GET', 'saved_actions/by-name/' + action_name)["data"]["id"]
		except:
			return False

	def delete_scheduled_action(self,action_id):
		return self.req('DELETE', 'saved_actions/' + str(action_id))

	def schedule_action(self,action_spec,get_results = False):
		action = self.req('POST', 'saved_actions/', action_spec)
		action_id = action["data"]["last_action"]["id"]
		expire_seconds = action["data"]["expire_seconds"]
		if self.debug:
			pp(action)

		if get_results:
			if not self.quiet:
				print("waiting for action id " + str(action_id) + " to " + str(self.action_complete_percent) + " complete.")
			result_info = self.get_action_results(action_id)
			return {
				"action_id" : action_id,
				"result_info" : result_info,
				"action" : action
			}
		else:
			return action_id

	def run_action(self,action_spec,get_results = False):
		action = self.req('POST', 'actions/', action_spec)
		action_id = action["data"]["id"]
		expire_seconds = action["data"]["expire_seconds"]
		if self.debug:
			pp(action)

		if get_results:
			if not self.quiet:
				print("waiting for action id " + str(action_id) + " to " + str(self.action_complete_percent) + " complete.")
			result_info = self.get_action_results(action_id)
			return {
				"action_id" : action_id,
				"result_info" : result_info,
				"action" : action
			}
		else:
			return action_id

	def get_action_results(self,action_id):
		action = self.req('GET', 'actions/' + str(action_id))["data"]
		expiration_time = parser.parse(action["expiration_time"])
		results = self.req('GET', 'result_info/action/' + str(action_id))["data"]
		result_info = results["result_infos"][0]
		while result_info['row_count_machines'] < (result_info['estimated_total'] * self.action_complete_percent) and datetime.now(timezone.utc).timestamp() < expiration_time.timestamp():
			if not self.quiet:
				print("Polling, {}/{}. Action expires in {} seconds.".format(result_info['row_count_machines'],result_info['estimated_total'], (expiration_time - datetime.now(timezone.utc)).seconds ))
			time.sleep(5)
			results = self.req('GET', 'result_info/action/' + str(action_id))["data"]
			result_info = results["result_infos"][0]
		return result_info

	def parse_action_outputs(self,outputs):
		actionout = {}
		for output in outputs["result_sets"]:
			for row in output["rows"]:
				key=row["data"][0][0]["text"]
				linenum=row["data"][1][0]["text"]
				text=row["data"][2][0]["text"]
				try:
					if key in actionout:
						actionout[key][linenum] = text
					else:
						actionout[key] = {
							linenum: text
						}
				except:
					if not self.quiet:
						print("get_action_output: unable to parse record:")
						pp(row)

		messages = []
		for md5 in actionout:
			logs = [None] * 5
			for logentry in actionout[md5]:
				for index in logentry:
					#print(md5 + " log index " + index)
					if md5 == "[no results]":
						continue
					#print(self.escape_ansi(actionout[md5][index]))
					#logs[int(index)]=escape_ansi(actionout[md5][index])
					try:
						logs[int(index)]=self.escape_ansi(actionout[md5][index])
					except:
						print("error adding logentry to message.")
			
			for log in logs:
				if log != None:
					messages.append(log)

		return messages

	def get_action_failed_output(self,action_id):
		outputquestion = {
			"selects": [
				{
					"sensor": {
						"name": "TanCD Tanium Action Output",
						"source_hash": self.get_sensor_hash("TanCD Tanium Action Output"),
						"parameters": [
							{
								"key": "||actionNumber||",
								"value": str(action_id)
							}
						]
					},
				}
			],
			"group": {
				'and_flag': True,
				'filters': [
					{
						'sensor': {
							'source_hash': self.get_sensor_hash("TanCD Tanium Action Failure"),
							'parameters': [
								{
									"key": "||actionNumber||",
									"value": str(action_id)
								}
							],
						},
						'operator': 'Equal',
						'value': 'True',
						'value_type': 'String',
						'ignore_case_flag': True,
					}				
				]
			}		
		}
		qid = self.ask_question(outputquestion)
		outputs = self.get_question_results(qid)
		if self.debug:
			print("get_action_failed_output question outputs object:")
			pp(outputs)
		#parsedoutput = self.parse_action_outputs(outputs["data"])
		return {"qid": qid, "data": self.parse_action_outputs(outputs)}

	def get_action_failed_computers(self,action_id):
		failedcomputersquestion = {
			"selects": [
				{
					"sensor": {
						"name": "Computer Name",
						"source_hash": self.get_sensor_hash("Computer Name")
					},
				},
				{
					"sensor": {
						"name": "Operating System",
						"source_hash": self.get_sensor_hash("Operating System")
					}
				}
			],
			"group": {
				'and_flag': True,
				'filters': [
					{
						'sensor': {
							'source_hash': self.get_sensor_hash("TanCD Tanium Action Failure"),
							'parameters': [
								{
									"key": "||actionNumber||",
									"value": str(action_id)
								}
							],
						},
						'operator': 'Equal',
						'value': 'True',
						'value_type': 'String',
						'ignore_case_flag': True,
					}				
				]
			}		
		}
		qid = self.ask_question(failedcomputersquestion)
		outputs = self.get_question_results(qid)
		if self.debug:
			print("get_action_failed_computers question outputs object:")
			pp(outputs)
		#parsedoutput = self.parse_action_outputs(outputs["data"])
		#return {"qid": qid, "data": self.parse_action_outputs(outputs)}
		#pp(outputs)
		computers=[]
		for output in outputs["result_sets"]:
			for row in output["rows"]:
				#pp(row["data"])
				#computers.append(row["data"][0][0]["text"])
				#print("computer name: " + row["data"][0][0]["text"])
				#print("operating system: " + row["data"][1][0]["text"])
				computers.append({
					'name': str(row["data"][0][0]["text"]),
					'os': str(row["data"][1][0]["text"])
				})
		return computers

	def get_action_failure(self,action_id):
		failurequestion = {
			"selects": [
				{
					"sensor": {
						"name": "Online",
						"source_hash": self.get_sensor_hash("Online")
					},
				}
			],
			"group": {
				'and_flag': True,
				'filters': [
					{
						'sensor': {
							'source_hash': self.get_sensor_hash("TanCD Tanium Action Failure"),
							'parameters': [
								{
									"key": "||actionNumber||",
									"value": str(action_id)
								}
							],
						},
						'operator': 'Equal',
						'value': 'True',
						'value_type': 'String',
						'ignore_case_flag': True,
					}				
				]
			}		
		}
		qid = self.ask_question(failurequestion)
		results = self.get_question_results(qid)
		#pp(results)
		#print("get_action_failure qid: " + str(qid))
		#print("get_action_failure output: ")
		#pp(len(results["result_sets"][0]["rows"]))
		if len(results["result_sets"][0]["rows"]) == 0:
			return False
		else:
			return True

	def get_action_output(self,action_id):
		outputquestion = {
			"selects": [
				{
					"sensor": {
						"name": "TanCD Tanium Action Output",
						"source_hash": tan.get_sensor_hash("TanCD Tanium Action Output"),
						"parameters": [
							{
								"key": "||actionNumber||",
								"value": str(action_id)
							}
						]
					}
				}
			]
		}
		qid = self.ask_question(outputquestion)
		outputs = tan.get_question_results(qid)

		if self.debug:
			print("get_action_output question results: ")
			pp(oututs)
			
		actionout = {}
		for output in outputs["result_sets"]:
			for row in output["rows"]:
				key=row["data"][0][0]["text"]
				linenum=row["data"][1][0]["text"]
				text=row["data"][2][0]["text"]
				try:
					if key in actionout:
						actionout[key][linenum] = text
					else:
						actionout[key] = {
							linenum: text
						}
				except:
					if not self.quiet:
						print("get_action_output: unable to parse record:")
						pp(row)

		if self.debug:
			print("action output data")
			pp(actionout)

		messages = []
		for md5 in actionout:
			logs = [None] * 5
			for logentry in actionout[md5]:
				for index in logentry:
					#print(md5 + " log index " + index)
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
					messages.append(log)

		return messages

	def run_sensors(self,sensors):
		if type(sensors) is str:
			sensors = [sensors]

		question = {
        	"selects": [
        	]
	    }
		for sensor in sensors:
			question["selects"].append({"sensor": { "name": sensor}})
		
		return self.ask_question(question)

	def ask_question(self,question):
		question_result = self.req('POST', 'questions/', question)
		return question_result['data']['id']

	def make_results_html(self,data):
		output="<table><tr>\n "
		for result in data["result_sets"]:
			for columnheader in result["columns"]:
				output+="<th>" + columnheader["name"] + "</th>"
			output+="</tr>\n"
			for row in result["rows"]:
				output+="<tr>\n "
				for column in row["data"]:
					output+="<td>" + column[0]["text"] + "</td>"
				output+="\n</tr>\n"
		output+="\n</table>\n<br>\n\n"
		return output

	def get_question_info(self, qid):
		questioninfo = self.req('GET', 'questions/' + str(qid))
		return questioninfo["data"]
	
	def get_question_results(self, qid):
		# Poll the result info metadata until 99% of endpoints have responded, then pull results.
		if qid in self.saved:
			qid = self.req('GET', 'result_data/saved_question/' + str(qid))['data']['result_sets'][0]['question_id']
		q = self.req('GET', 'result_info/question/' + str(qid))
		q  = q['data']['result_infos'][0]

		while q['tested'] < (q['estimated_total'] * self.question_complete_percent):
			if not self.quiet:
				print("Polling qid {}, {}/{}.".format(qid,q['tested'],q['estimated_total']))
			q = self.req('POST', 'result_info/question/' + str(qid))['data']['result_infos'][0]
			time.sleep(1) # Polling rate
		results = self.req('GET', 'result_data/question/{}'.format(qid))
		if self.debug:
			print("get_question_results raw data")
			pp(results)
		return results["data"]

	def escape_ansi(self, line):
		ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
		try:
			return ansi_escape.sub('', line)
		except:
			return 'no output'