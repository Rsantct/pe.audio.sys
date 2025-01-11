#!/bin/bash

function loop_until_ok {

    CMD=$1

    retries=5
    count=0
    until $CMD 2>/dev/null || [[ $count -ge $retries ]]; do
        sleep .2
        ((count++))
    done

    if [[ $count -ge $retries ]]; then
        echo "Problems with: ""$CMD"
        return 1
    fi

    return 0
}


function loop_until_result {

    CMD=$1
    PATTERN=$2

    retries=5
    count=0
    while [[ $count -le $retries ]]; do

        RESULT=$($CMD)

        if [[ $RESULT == *"$PATTERN"* ]]; then
            break
        fi

        sleep .2
        ((count++))

    done

    if [[ $count -ge $retries ]]; then
        echo "Problems with: ""$CMD"
        return 1
    fi

    return 0
}


function get_jack_rate {

    if [[ ! $1 ]]; then
        echo "Need a parameter name, example '-r'"
        exit 1
    fi

    arg_name=$1

    pid=$(pidof jackd)

    cmdline=$(ps -p "$pid" -o command=)

    # array form
    args=($cmdline)


    for ((i=0; i<${#args[@]}; i++)); do
        if [[ "${args[$i]}" == "$arg_name" ]]; then

            # Check if there is a value after the argument name
            if (( i+1 < ${#args[@]} )); then
                arg_value="${args[$((i+1))]}"
            else
                echo "Error: Argument $arg_name requires a value." >&2
                return 1
            fi
            break
        fi
    done

    RATE=$arg_value
}


function camilla_release {

    j_partner_name=$1

    for PORT in "out_0" "out_1"; do

        loop_until_result "jack_lsp -c cpal_client_out:""$PORT" "$j_partner_name"
        RESULT="${RESULT//$'\n'}"

        loop_until_ok "jack_disconnect $RESULT"

    done
}


function insert_camilla {

    for PRE_PORT in "1" "2"; do

        # get pre_in_loop sources
        PRE_WIRE=$(jack_lsp -c pre_in_loop:input_$PRE_PORT)
        PRE_WIRE="${PRE_WIRE//$'\n'}"

        PRE_SRC=$(echo $PRE_WIRE | cut -d " " -f 2)

        # Camilla jack ports are 0 and 1
        CPAL_PORT=$(($PRE_PORT - 1))

        jack_disconnect $PRE_WIRE                                                       2>/dev/null

        jack_connect "$PRE_SRC"                         cpal_client_in:in_"$CPAL_PORT"  2>/dev/null

        jack_connect cpal_client_out:out_"$CPAL_PORT"   pre_in_loop:input_"$PRE_PORT"   2>/dev/null

    done
}


# Retrieving the JACK sample rate
get_jack_rate "--rate"

if [[ ! $RATE ]]; then
    get_jack_rate "-r"
fi

if [[ ! $RATE ]]; then
    echo "Unable to find the jack sample rate."
    exit 1
fi


# CamillaDSP config file path
CFG_PATH=pe.audio.sys/config/camilladsp_compressor.yml

# CamillaDSP log file
LOG_PATH="$HOME"/pe.audio.sys/log/camilladsp.log

# Restarting CamillaDSP
killall camilladsp 2>/dev/null
camilladsp  -r $RATE \
            --wait -a 127.0.0.1 -p 1234 \
            --logfile "$LOG_PATH" \
            $CFG_PATH &

# Disconnecting auto connected jack ports
camilla_release "system"

# Inserting
insert_camilla

exit 0
