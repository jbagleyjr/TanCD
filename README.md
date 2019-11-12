# TanCD
##### Tanium content Continuous Deployment pipeline.

```
tanium.py:      Python class that implements the Tanium REST API.
get_sensor.py:  Gets a sensor from tanium and stores it in a file.
get_package.py: Gets a package from tanium and stores it in a file.
put_sensor.py:  Add or update a sensor on the tanium server from a file.
put_package.py: Add or update a package on the tanium server from a file.
check_*.py:     Checks that content ahears to policy for naming, caching, etc.. (defined in content.cfg).
analyze_sensors.py:   Runs static analysis on sensor scripts.
test_*.py:      Executes sensors/packages on the Tanium server and collects performance data.
content.cfg:    Defines settings to use.
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
1.  Create a GIT repo.
2.  Clone this repo as a submodule
3.  Add "test_sensors.xml", "test_packages.xml", and "prod_sensors.xml" to your Tanium test server
