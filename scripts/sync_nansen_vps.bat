@echo off
REM sync_nansen_vps.bat — Task Scheduler wrapper for Nansen snapshot sync
REM Trigger: daily 08:10 VN local (=01:10 UTC), after Nansen bot cron 08:00 VN
REM Per operator KÝ 29/08 · resolves Task Scheduler direct-python fire issue.

set REPO=D:\Data back test\whale_data
set PYTHON=C:\Users\Hello\AppData\Local\Programs\Python\Python314\python.exe
set SCRIPT=%REPO%\scripts\sync_nansen_snapshots_to_vps.py
set LOG=%REPO%\data\logs\sync_task.log

cd /d "%REPO%"

echo. >> "%LOG%"
echo === RUN %DATE% %TIME% === >> "%LOG%"
"%PYTHON%" "%SCRIPT%" >> "%LOG%" 2>&1

exit /b %ERRORLEVEL%
