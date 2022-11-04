#!/bin/bash


# This program is called from the libresport --onevent option
# in order to connect <librespot:output> to <librespot_loop:input>
#
# --onevent runs a program by providing some useful environmet variables.
#
# Binding ports is necessary because the libresport JACKAUDIO backend behavoir:
# - The jack port does not emerge until first time playing.
# - There is not any option to autoconnect to any destination jack port.


if [[ $PLAYER_EVENT == "started" || $PLAYER_EVENT == "playing" ]]; then

    conns=$(jack_lsp -c librespot_loop\:input)

    if [[ $conns != *"librespot:out"* ]]; then
        jack_connect librespot:out_0 librespot_loop:input_1 1>/dev/null 2>&1
        jack_connect librespot:out_1 librespot_loop:input_2 1>/dev/null 2>&1
    fi

fi

