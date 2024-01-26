#!/bin/bash

# export package_name="install perf include"
# [ -f /opt/Tanium/TaniumClient/perf/perf.sh ] && . /opt/Tanium/TaniumClient/perf/perf.sh

##
# truncates perf log down to the most recent 100 entries

if [ -f /opt/Tanium/TaniumClient/perf/perf.log ]
then
	tail -n 50 /opt/Tanium/TaniumClient/perf/perf_action.log > /tmp/perf_action.log
	mv -f /tmp/perf_action.log /opt/Tanium/TaniumClient/perf/perf_action.log
fi

