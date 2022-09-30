#!/bin/sh

while true; do

    echo "--- STATE"
    cat pe.audio.sys/.state | jq

    echo "--- TONE_MEMO"
    cat pe.audio.sys/.tone_memo | jq

    echo "--- AUX_INFO"
    cat pe.audio.sys/.aux_info | jq

    sleep 1
    clear

done
