#!/bin/bash

if [[ $1 == 'stop' ]]; then
    mpd --kill
    exit 0
fi

mpd

