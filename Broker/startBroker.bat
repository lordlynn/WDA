@echo off

set configDir=%CD%
set configFile=mosquitto.conf 
set file=%configDir%\%configFile%

cd C:\Program Files\mosquitto

.\mosquitto -c "%file%" -v