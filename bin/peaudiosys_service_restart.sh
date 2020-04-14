#!/bin/bash

serverPath="pe.audio.sys/share/services/server.py"

function main {

    # Killing the running service:
    # (triple quoted is needed for this to work)
    pkill -KILL -f """server.py $svc"""
    if [[ $opc == *'stop'* ]]; then
        return
    fi
    sleep .25

    # Reading TCP address and port from the pe.audio.sy config file
    ADDR=$( grep peaudiosys_address ~/pe.audio.sys/config.yml | awk '{print $NF}' )
    ADDR=${ADDR//\"/}; CTL_ADDR=${ADDR//\'/}
    PORT=$( grep peaudiosys_port ~/pe.audio.sys/config.yml | awk '{print $NF}' )
    if [[ ! $ADDR ]]; then
        echo ERROR reading config.yml
        exit -1
    fi

    if [[ $svc == 'peaudiosys' ]]; then
        :
    elif [[ $svc == 'preamp' ]]; then
        ADDR='localhost'
        (( PORT += 1 ))
    elif [[ $svc == 'players' ]]; then
        ADDR='localhost'
        (( PORT += 2 ))
    else
        echo $svc NOT valid
        exit -1
    fi

    # Launching again the service.
    # (i) It is IMPORTANT to redirect stdout & stderr to keep it alive even
    #     if the launcher session has been closed (e.g. a crontab job),
    #     except if -v --verbose is indicated
    if [[ $opc == *"-v"* ]]; then
        python3 "$HOME"/"$serverPath" "$svc" "$ADDR" "$PORT" -v &
    else
        python3 "$HOME"/"$serverPath" "$svc" "$ADDR" "$PORT" >/dev/null 2>&1 &
    fi
}


svc=$1
opc=$2

if [[ -z $svc ]]; then
    echo "usage:    peaudiosys_service_restart.sh   <service>  [stop | --verbose]"
    echo ""
    echo "          <service>   peaudiosys | preamp | players | all"
    echo "          --verbose   will keep messages to console,"
    echo "                      otherways will redirect to /dev/null"
    exit 0
fi

# a little trick, you can use the former 'control' service name
if [[ $svc == 'control' ]]; then
    svc=peaudiosys
fi

if [[ $svc == 'all' ]]; then
    declare -a svcs=("preamp" "players" "peaudiosys")
else
    declare -a svcs=("$svc")
fi

for svc in "${svcs[@]}"; do
   main
done
