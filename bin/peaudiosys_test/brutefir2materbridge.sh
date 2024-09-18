#!/bin/bash

pkill meterbridge

meterbridge -c 3 -t dpm -n Meter_L \
    brutefir:lo.L \
    brutefir:mi.L \
    brutefir:hi.L \
    1>/dev/null 2>&1 &

meterbridge -c 3 -t dpm -n Meter_R \
    brutefir:lo.R \
    brutefir:mi.R \
    brutefir:hi.R \
    1>/dev/null 2>&1 &

