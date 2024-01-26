#!/bin/bash

#export package_name="install perf include"
#[ -f /opt/Tanium/TaniumClient/perf/perf.sh ] && . /opt/Tanium/TaniumClient/perf/perf.sh

##
# Measures the performance and exit code value of each sensor and package

start=$(date +%s)

if [ "null$sensor_name" != "null" ]
then
	trap sensorperfcollect EXIT
fi

if [ "null$package_name" != "null" ]
then
	export action_id=$(echo "$PWD" | awk -F/ '{ print $NF }' | awk -F_ '{ print $2 }')
	trap packageperfcollect EXIT
fi


function sensorperfcollect() {
	rv=$?
	runtime=$(($(date +%s)-start))
	times=$(times | tr '\n' ';' | tr ' ' ';')
	date=$(date +%s)

	echo "$date;$sensor_name;$runtime;$times$rv" >> /opt/Tanium/TaniumClient/perf/perf.log
	/opt/Tanium/TaniumClient/perf/perf_log_rotate.sh
}

function packageperfcollect() {
	rv=$?
	runtime=$(($(date +%s)-start))
	times=$(times | tr '\n' ';' | tr ' ' ';')

	echo "$action_id;$package_name;$runtime;$times$rv" >> /opt/Tanium/TaniumClient/perf/perf_action.log
	/opt/Tanium/TaniumClient/perf/perf_action_log_rotate.sh
}

