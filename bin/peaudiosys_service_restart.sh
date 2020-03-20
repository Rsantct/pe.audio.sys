#!/bin/bash

svc=$1
opc=$2

if [[ -z $svc ]]; then
    echo "usage:    peaudiosys_service_restart.sh   <service>  [stop | --verbose]"
    echo ""
    echo "          --verbose   will keep messages to console,"
    echo "                      otherways will redirect to /dev/null"
    exit 0
fi

# a little trick, you can use the former 'control' service name
if [[ $svc = 'control' ]]; then
    svc=pasysctrl
fi

# Killing the running service:
# (triple quoted is needed for this to work)
pkill -KILL -f """server.py $svc"""
if [[ $opc == 'stop' ]]; then
    exit 0
fi
sleep .25

# Reading addresses and ports from the pe.audio.sy config file
SRV_ADDR=$( grep "$svc"_address ~/pe.audio.sys/config.yml | awk '{print $NF}' )
SRV_ADDR=${SRV_ADDR//\"/}; SRV_ADDR=${SRV_ADDR//\'/}
SRV_PORT=$( grep "$svc"_port ~/pe.audio.sys/config.yml | awk '{print $NF}' )

if [[ ! $SRV_ADDR ]]; then
    echo unknown \'$svc\'
    exit -1
fi

# Launching again the service.
# (i) It is IMPORTANT to redirect stdout & stderr to keep it alive even
#     if the launcher session has been closed (e.g. a crontab job),
#     except if -v --verbose is indicated
if [[ $opc == *"-v"* ]]; then
    python3 ~/pe.audio.sys/share/server.py "$svc" "$SRV_ADDR" "$SRV_PORT" "$2" &
else
    python3 ~/pe.audio.sys/share/server.py "$svc" "$SRV_ADDR" "$SRV_PORT" "$2" 1>/dev/null 2>&1 &
fi
