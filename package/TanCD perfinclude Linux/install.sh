#!/bin/bash

export package_name="install perf include"
[ -f /opt/Tanium/TaniumClient/perf/perf.sh ] && . /opt/Tanium/TaniumClient/perf/perf.sh

if [ -d /opt/Tanium/TaniumClient/perf ]
then
	cp -f ./*.sh /opt/Tanium/TaniumClient/perf/
	chmod a+rx /opt/Tanium/TaniumClient/perf/*.sh
else
	mkdir -p /opt/Tanium/TaniumClient/perf
	cp -f ./*.sh /opt/Tanium/TaniumClient/perf/
	chmod a+rx /opt/Tanium/TaniumClient/perf/*.sh
fi
