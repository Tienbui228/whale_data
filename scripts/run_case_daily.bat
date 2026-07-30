@echo off
set PYTHONUTF8=1
set LOGFILE=D:\Data back test\whale_data\data\logs\case_daily.log
set SCRIPT=D:\Data back test\whale_data\scripts\case_daily.py
set PYTHON=C:\Users\Hello\AppData\Local\Programs\Python\Python314\python.exe
echo === %date% %time% === >> "%LOGFILE%"
"%PYTHON%" "%SCRIPT%" >> "%LOGFILE%" 2>&1
