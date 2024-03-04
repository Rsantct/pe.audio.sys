#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.


# NOTICE `peaudio_backup.list` (--files-from) CANNOT manage wildcards, so specify each file or directory.


# Default destination folder can be changed from command line
destdir="$HOME/tmp"


function print_help {
    echo
    echo "    A tool to backup pe.audio.sys"
    echo
    echo "    Usage:  peaudiosys_backup -b [destinatior_dir]"
    echo
    echo "    (Restoring is left to be done manually)"
    echo
    echo "    You can use an external USB disk:"
    echo
    echo "    First identify the external disk, and mount it"
    echo
    echo "        sudo fdisk -l   ---> for example  /dev/sda1"
    echo
    echo "        sudo mkdir -p /media/pincho"
    echo "        sudo mount -o user,umask=0000 /dev/sda1 /media/pincho"
    echo
    echo "    Then proceed to backup"
    echo
    echo "        peaudiosys_backup  -b  /media/pincho "
    echo
    echo "    And when finished:"
    echo
    echo "        sudo unmount /media/pincho"
    echo

}


function do_backup {

    mkdir -p "$destdir"/"$HOSTNAME"

    # -j bzip2
    # -J xzip  slower but ~60% smaller

    tar --directory $HOME                   \
        --absolute-names                    \
        --verbose                           \
        -c -j                               \
        -f "$tarpath"                       \
                                            \
        --ignore-failed-read                \
        --wildcards                         \
        --exclude=*.wav                     \
        --exclude=*.dat                     \
        --exclude=*.png                     \
        --exclude=*/doc/*                   \
        --exclude=*loudspeakers/*example*   \
        --exclude=*loudspeakers/*sample*    \
        --exclude=*loudspeakers/*test*      \
        --exclude=*/www/images/*            \
        --exclude=*.pyc                     \
        --exclude=*__pycache__*             \
        --exclude=*.sample                  \
        --exclude=*.example                 \
        --verbatim-files-from               \
        --files-from="$listpath"            \
        1>$logpath 2>&1


    echo -n "(peaudiosys_backup.sh) "
    ls -sh "$tarpath"

}



if [[ $1 == *"-b"* ]]; then


    if [[ $2 ]]; then
        destdir="$2"
    fi

    timestamp=$(date +%Y%m%d_%H%M)
    tarpath="$destdir"/"$HOSTNAME"/pe.audio.sys_"$timestamp".tar.gz
    logpath="${tarpath/tar.gz/log}"

    thisfname=$0
    listpath="${thisfname/sh/list}"

    echo
    echo "READING LIST OF FILES FROM:"
    echo "    "$listpath
    echo
    echo "TAR & LOG FILES:"
    echo "    "$tarpath
    echo "    "$logpath


    echo
    read -p "Are you sure?: (y/N) " ans
    if [[ $ans != *"y"*  && $ans != *"Y"* ]];then
        echo 'Bye!'
        exit 0
    fi

    do_backup

else
    print_help

fi
