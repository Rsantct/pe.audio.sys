#!/bin/bash

while true; do

    echo "--- STATE"
    cat pe.audio.sys/.state | jq
    
    echo "--- TONE_MEMO"
    cat pe.audio.sys/.tone_memo | jq
    
    sleep 1
    clear
done
