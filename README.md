# TanCD
Tanium content Continuous Deployment pipeline.

tanium.py:      Python class that implements the Tanium REST API.
get_sensor.py:  Gets a sensor from tanium and stores it in a file.
get_package.py: Gets a package from tanium and stores it in a file.
put_sensor.py:  Add or update a sensor on the tanium server from a file.
put_package.py: Add or update a package on the tanium server from a file.
check_*.py:     Checks that content ahears to policy for naming, caching, etc.. (defined in content.cfg).
analyze_sensors.py:   Runs static analysis on sensor scripts.
test_*.py:      Executes sensors/packages on the Tanium server and collects performance data.
content.cfg:    Defines settings to use.


Sensors:
    - MGC Tanium Action Output
    - MGC Tanium Action Failure
    - sensor performance
    - MGC Package Performance

rename these to:
    > TanCD Tanium Action Output
    - TanCD Tanium Action Failure
    - TanCD Sensor Performance
    - TanCD Package Performance

Packages:
    - install MGTools

new packages:
    - TanCD perfinclude Windows
    - TanCD perfinclude Linux

How to package and deliver TanCD Tanium Content?  Two sets:

1.  Everything is installed in your test environment
2.  Everything except these are installed in production:
    - perfinclude packages
    - sensor performance sensor

