#!/bin/bash

# Loops displaying the pe.audio.sys state dict, filtering
# fields by the command line given patterns. Example:
#
#       peaudiosys_view_state.sh level headroom
#

tmp=""

for arg in "$@"; do

    echo "    ""$arg"
    tmp+="$arg""\|"

done

sleep 1; clear

tmp=${tmp::-2}

while true; do

    echo "--- TONE_MEMO"
    cat pe.audio.sys/.tone_memo | jq

    echo "--- AUX_INFO"
    cat pe.audio.sys/.aux_info | jq

    echo "--- STATE"
    cat ~/pe.audio.sys/.state | jq | grep "$tmp" --color


    sleep 1
    clear

done
