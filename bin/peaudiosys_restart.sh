#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.


function do_stop {

    echo '(i) STOPPING pe.audio.sys'
    $HOME/pe.audio.sys/start.py stop

}


function do_start {

    if [[ ! $XDG_CURRENT_DESKTOP ]]; then
        # Needed for jackd when called w/o X environment:
        export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
    fi

    # (i) Unattended restarts in headless machines can have a weird behavior,
    #     so will retry restarting if necessary up to 3 times.
    tries=1
    if [[ $1 == *'-r'* ]]; then
        tries=3
    fi
    c=1
    while [[ $c -le $tries ]]; do

        echo "try #"$c" "$(date) > $HOME/pe.audio.sys/log/peaudiosys_restart_tries.log
        echo '(i) RESTARTING pe.audio.sys (all printouts hidden to /dev/null)'
        echo '    Startup process logged in <pe.audio.sys/log/start.log>'
        $HOME/pe.audio.sys/start.py all --log 1>/dev/null 2>&1 &

        sleep 5
        echo '    waiting for the server to be running ... .. .'
        n=60
        ok='false'
        while [[ $n -gt 0 ]]; do
            if [[ $(pgrep -fla "server.py peaudiosys") ]]; then
                ok='true'
                break
            fi
            sleep 1
            ((n-=1))
        done

        if [[ $ok == 'true' ]]; then
            echo "    OK, server runing in "$((60-n))"s"
            break
        else
            if [[ $c -lt $tries ]]; then
                echo "    server NOT detected in 60s, retrying ..."
            else
                echo "    server NOT detected during "$c" attempts. Bye."
            fi
        fi

        ((c+=1))

    done

}


if [[ $1 == 'stop' ]]; then
    do_stop

elif [[ ! $1 || $1 == *'start' ]]; then
    do_start $2

else
    echo
    echo "USAGE:   peaudiosys_restart.sh  [ start [-r]  |  stop ]"
    echo
    echo "         -r   will retry up to 3 times useful when unattended restarting"
    echo
    echo "         Startup process will be logged in <pe.audio.sys/log/start.log>"
    echo "         For further debugging run manually from a terminal:"
    echo "             peaudio.sys/start.py all & "
    echo

fi
