# TanCD
##### Tanium content Continuous Deployment pipeline.

*This is unofficial Tanium content. These have not been tested or approved by anyone at Tanium.*

Intended use is to pull this GIT into your internal GIT repo as a sub-module.  This repo should not
contain any of your internally developed Tanium content, only the workflow to apply a CD pipeline to
your Tanium Content development workflow.

Files:
```
tanrest.py:     Python class that implements the Tanium REST API.
get_sensor.py:  Gets a sensor from tanium and stores it in a file.
get_package.py: Gets a package from tanium and stores it in a file.
put_sensor.py:  Add or update a sensor on the tanium server from a file.
put_package.py: Add or update a package on the tanium server from a file.
check_*.py:     Checks that content ahears to policy for naming, caching, etc.. (defined in content.cfg).
analyze_sensors.py:   Runs static analysis on sensor scripts.
test_*.py:      Executes sensors/packages on the Tanium server and collects performance data.
content.cfg:    Defines settings to use.
*.xml:          Sensors and packages used by TanCD.
```

Sensors:
- TanCD Tanium Action Output
- TanCD Tanium Action Failure
- TanCD Sensor Performance
- TanCD Package Performance

Packages:
- TanCD perfinclude Windows
- TanCD perfinclude Linux

Quick start:
1.  Create a GIT repo to store your internally developed Tanium Content (sensors and packages).
2.  Clone this repo as a submodule.
  - `git submodule add https://github.com/jbagleyjr/TanCD.git`
3.  Add "test_sensors.xml", "test_packages.xml", and "prod_sensors.xml" to your Tanium test server.
4.  (optional) Add "prod_sensors.xml" to your production Tanium server.
5.  (optional) Verify the tanrest class works as expected by adding the included Chuck Norris Fact sensor to your tanium server.
   - `cd TanCD; python3 put_sensor.py --server 139.181.111.21 --username tanium --sensor 'Chuck Norris Fact'`
6.  Setup your CI/CD pipeline!  You can use the scripts and yml under gitlab-ci as a starting point, but copy them into your own GIT repo.

All of the command line python programs are setup to read/write sensor and package files into 'sensor' and 'package'
sub-directories of the current directory.  This allows 'TanCD' content to remain in a separate GIT repo from your
Tanium content assuming that you invoke the commands from the parent directory.  As in;

## Get a sensor
`python3 TanCD/get_sensor.py --server <your tanium server> --username <your tanium username> --password <your password> --sensor "<your new sensor>"`

## Check a sensor
`python3 TanCD/check_sensor.py --sensor "<your new sensor>"`


