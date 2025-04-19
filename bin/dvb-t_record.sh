#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

# You need a DVB-T dongle, also the 'dvb-apps' and 'scan' packages,
# please see details at pe.audio.sys/pe.audio.sys/doc

#
# NOTICE:
# If your recording time is greater than ~ 6 hours, the resulting wav file
# header cannot suport the actual file size, so wav readers will ignore
# recorded samples beyond ~ 4 Gb.
#
# A workaround is to ignore the wav header. You can use Audacity then import
# the radio_xxxx.wav as RAW DATA (signed 16 bit PCM default endianness 2 ch 48 KHz)
#


# Put here the channel name as per ~/.mplayer/channels.conf
#
channel="Radio Clasica HQ A52"


# 'Radio Clasica HD A52' is codified in Dolby Digital AC-3 (5.1 channels 48KHz/float32)
#  It only carries FL and FR channels with volume reduced about 12 dB.
#  Mplayer will convert to 16 bit in order to reduce the recorded file size,
#  also will apply a volume gain (12 dB should work fine, but 9 dB is safer)
#
dB_gain=9



if [[ $1 == *'-h'* || $1 == *'help'* ]]; then
    echo
    echo "USAGE:   dvb-t_record.sh  [ \"Channel Name\"  | --stop ]"
    echo
    echo "         If no channel name, will use the default channel inside this script:"
    echo "         ""$channel"
    echo
    echo "         Files will be stored under ~/dvb-t/"
    echo
    exit 0


elif [[ $1 == *'-s'* || $1 == *'stop'* ]]; then

    echo STOPPING RECORDING.

    # mplayer listens to SIGINT for a clean program stop.
    pkill -SIGINT -f "mplayer dvb"

    exit 0

else
    if [[ $1 ]]; then
        channel=$1
    fi
fi


if [[ ! $(grep -F "$channel" .mplayer/channels.conf) ]]; then
    echo "Bad channel name, exiting."
    exit 0
fi


mkdir -p ~/dvb-t

fname=~/dvb-t/dvb-t_"$(date '+%Y%m%d_%H%M%S')".wav

mplayer "dvb://""$channel" \
        -nolirc -quiet  \
        -ao pcm:waveheader:file=$fname \
        -af volume=$dB_gain,format=s16le &

echo
echo RECORDING TO $fname ...
echo

