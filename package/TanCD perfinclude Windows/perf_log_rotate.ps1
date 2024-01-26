$maxlines = 100
$logfile = 'c:\mgctanium\perf.log'

(get-content $logfile -tail $maxlines -readcount 0) | out-file $logfile
