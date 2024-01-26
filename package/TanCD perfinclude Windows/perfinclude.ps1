$ErrorActionPreference = "Stop"
$lockfile = “c:\mgctanium\perflock.lck”

function measurescript {
    $PID | Out-File $lockfile
    $random = get-random -maximum 7
    while ( test-path "c:\mgctanium\tmp$random.ps1" ) {
        $random = get-random -maximum 7
    }
    $invocation | out-file c:\mgctanium\debug.out
    [string]$invocation.MyCommand | out-file c:\mgctanium\tmp$random.ps1
    $start = Get-Date -UFormat %s
    & c:\mgctanium\tmp$random.ps1 | out-null
    if ($?) {
        $exitval=0
    }
    else {
        $exitval=1
    }
    $end = Get-Date -UFormat %s
    $runtime = $end - $start
    #write-host "runtime: $runtime"
    #write-host "exitval: $exitval"
    #write-host "sensor_name: $sensor_name"
    $timestamp=[int](Get-Date -UFormat %s)
    "$timestamp;$sensor_name;$runtime;;;;;$exitval" | out-file -append -filepath c:\mgctanium\perf.log
    & C:\mgctanium\perf_log_rotate.ps1
    remove-item C:\mgctanium\tmp$random.ps1
    remove-item $lockfile
}

If (Test-Path $lockfile) {
    $lastWrite = (get-item $lockfile).LastWriteTime
    $timespan = new-timespan -hours 1

    if (((get-date) - $lastWrite) -gt $timespan) {
        measurescript
    } 
}
else {
    measurescript
}
