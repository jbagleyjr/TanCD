$installdir="c:\mgctanium"

If ( -not (Test-Path "$installdir" -PathType Container)) {
    mkdir "$installdir"
}


copy perfinclude.ps1 $installdir
copy perf_log_rotate.ps1 $installdir

