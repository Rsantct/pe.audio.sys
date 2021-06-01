#!/bin/bash


# The file which keeps the amplifier power outlet state
amp_file=$HOME/.amplifier


function save_state {

    if   [[ $new_state == '1' || $new_state == 'on' ]]; then
        echo 'on'   > $amp_file

    elif [[ $new_state == '0' || $new_state == 'off' ]]; then
        echo 'off'  > $amp_file

    else
        echo "unknown amp state"
        echo '?'    > $amp_file

    fi

}


function get_current_state {

    # Some 'ampli.sh' user script can output multiple lines for a
    # multiple power socket strip, so lets filter the one labeled *amp*
    curr_state=$($amp_mger | grep -i amp | tail -c4 | xargs)


    # If not luck, maybe we got a simple output result from 'ampli.sh'
    if [[ ! $curr_state ]];then
        curr_state=$($amp_mger)
    fi

    if [[ ! $curr_state ]];then
        curr_state="?"

    elif [[ $curr_state == '1' ]]; then
        curr_state='on'

    elif [[ $curr_state == '0' ]]; then
        curr_state='off'

    fi
}



# The user script that manages the amplifier power outlet
amp_mger=$(grep ^amp_manager pe.audio.sys/config.yml | xargs | cut -d\  -f2)
if [[ ! $amp_mger ]]; then
    amp_mger=$HOME/bin/ampli.sh
fi
# (replacing the tilde with full path to home)
amp_mger="${amp_mger/#\~/$HOME}"
if [[ ! -f "$amp_mger" ]]; then
    echo "ERROR amp manager script not found: ""$amp_mger"
    exit 0
fi


# Getting the current state
get_current_state
new_state=$curr_state


## Reading option from command line

# A) Just output the current state
if [[ ! $1 ]]; then
    echo $curr_state
    exit 0


# B) Toggle
elif  [[ $1 == 'toggle' || $1 == *'-t'* ]]; then

    if [[ $curr_state == 'on' ]]; then
        new_state='off'
    elif [[ $curr_state == 'off' ]]; then
        new_state='on'
    fi


# C) Switch ON
elif [[ $1 == 'on' || $1 == '1' ]]; then

    new_state='on'


# D) Switch OFF
elif [[ $1 == 'off' || $1 == '0' ]]; then

    new_state='off'


# E) Bad option
else

    echo "bad argument, use: on, 1, off, 0"
    exit 0

fi


# Doing things
$amp_mger $new_state
save_state
