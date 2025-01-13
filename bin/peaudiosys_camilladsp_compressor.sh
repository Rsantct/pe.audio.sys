#!/bin/bash

# Try running a COMMAND ($1) up to 5 times until there are no execution errors
function loop_until_ok {

    CMD=$1

    retries=5
    count=0
    until $CMD 2>/dev/null || [[ $count -ge $retries ]]; do
        sleep .2
        ((count++))
    done

    if [[ $count -ge $retries ]]; then
        echo "Problems running: ""$CMD"
        return 1
    fi

    return 0
}


# Try running a COMMAND ($1) up to 5 times until the result includes a PATTERN ($2)
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
        echo "Void: ""$CMD"
        return 1
    fi

    return 0
}

# Release all IN/OUT connections in camilla `cpal_client`jack ports
function camilla_release {

    j_partner_name=$1

    for PORT in "out_0" "out_1"; do

        loop_until_result "jack_lsp -c cpal_client_out:""$PORT" "$j_partner_name"
        RESULT="${RESULT//$'\n'}"

        if [[ $RESULT ]]; then
            loop_until_ok "jack_disconnect $RESULT"
        fi

    done
}


function camilla_insert {

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

# Returns the argument $JACK_ARG from the given alsa backend parameter ($1),
# e.g. '--rate' from the running JACK command line
function get_jack_alsa_param {

    if [[ ! $1 ]]; then
        echo "Need a parameter name, example '-r'"
        exit 1
    fi

    arg_name=$1

    pid=$(pidof jackd)

    # Example: `jackd -R -d alsa -d hw:DX,0 -p 512 -n 2 -r 44100 --softmode`
    cmdline=$(ps -p "$pid" -o command=)


    # Leaving only the alsa parameters: `-d hw:DX,0 -p 512 -n 2 -r 44100 --softmode`
    alsa_pos=$(echo "$cmdline" | awk -v what="alsa " '{print index($0, what)}')
    (( alsa_pos += 4 ))
    cmdline="${cmdline:$alsa_pos}"

    # convert to an array
    args=($cmdline)

    arg_value=''
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

    JACK_ARG=$arg_value
}


# Returns the alsa device $ALSA_DEV from the running JACK command line
function get_jack_alsa_device {

    get_jack_alsa_param "--device"

    if [[ ! $JACK_ARG ]]; then
        get_jack_alsa_param "-d"
    fi

    if [[ ! $JACK_ARG ]]; then
        echo "Unable to find the jack ALSA device."
        exit 1
    fi

    ALSA_DEV="$JACK_ARG"
}


# Returns the sample rate $RATE from the running JACK command line
function get_jack_samplerate {

    get_jack_alsa_param "-rate"

    if [[ ! $JACK_ARG ]]; then
        get_jack_alsa_param "-r"
    fi

    if [[ ! $JACK_ARG ]]; then
        echo "Unable to find the jack sample rate."
        exit 1
    fi

    RATE="$JACK_ARG"
}

# JACK ALSA device $ALSA_DEV --not used--
#get_jack_alsa_device

# JACK sample rate $RATE
get_jack_samplerate

# CamillaDSP config file path
CFG_PATH=pe.audio.sys/config/camilladsp_compressor.yml

# CamillaDSP log file
LOG_PATH="$HOME"/pe.audio.sys/log/camilladsp.log

# MUTING pe.audio.sys
control mute on 1>/dev/null

# Running CamillaDSP
killall camilladsp 2>/dev/null

if [[ ! $(pidof camilladsp) ]]; then

    camilladsp  -r $RATE \
                --wait -a 127.0.0.1 -p 1234 \
                --logfile "$LOG_PATH" \
                $CFG_PATH &
fi

# Disconnecting auto connected jack ports
camilla_release "system"

# Inserting
camilla_insert

# UNMUTING pe.audio.sys
control mute off 1>/dev/null

exit 0
