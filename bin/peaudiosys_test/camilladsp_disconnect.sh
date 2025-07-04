#!/bin/bash

exec > /dev/null 2>&1


function camilla_off {

    jack_disconnect     cpal_client_in:in_0     pre_in_loop:output_1
    jack_disconnect     cpal_client_in:in_1     pre_in_loop:output_2
    jack_disconnect     cpal_client_out:out_0   brutefir:in.L
    jack_disconnect     cpal_client_out:out_1   brutefir:in.R

    jack_connect        pre_in_loop:output_1    brutefir:in.L
    jack_connect        pre_in_loop:output_2    brutefir:in.R
}


function camilla_on {

    jack_disconnect     pre_in_loop:output_1    brutefir:in.L
    jack_disconnect     pre_in_loop:output_2    brutefir:in.R

    jack_connect        cpal_client_in:in_0     pre_in_loop:output_1
    jack_connect        cpal_client_in:in_1     pre_in_loop:output_2
    jack_connect        cpal_client_out:out_0   brutefir:in.L
    jack_connect        cpal_client_out:out_1   brutefir:in.R
}


if [[ $1 = "on" ]]; then
    camilla_off
else
    camilla_on
fi
