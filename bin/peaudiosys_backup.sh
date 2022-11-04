#!/bin/bash

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

function print_help {
    echo
    echo "    A tool to backup or restore pe.audio.sys files to/from"
    echo "        tmp/peaudiosys.bak_YYYYMMDD.tar.bz2"
    echo
    echo "    usage:"
    echo
    echo "      peaudiosys_backup.sh  --backup"
    echo "      peaudiosys_backup.sh  --restore [path/to/tarfile*]"
    echo
    echo "          * if not given, will use the most recent found."
    echo
}


function do_backup {
    cd
    mkdir -p tmp

    now=$(date +%Y%m%d)
    me=$(hostname)
    tarpath=$HOME/tmp/peaudiosys.bak_"$me"_"$now".tar.xz

    # -j bzip2
    # -J xzip  slower but ~60% smaller

    tar --directory $HOME                   \
        --absolute-names                    \
        -c -j -f "$tarpath"                 \
                                            \
        --ignore-failed-read                \
                                            \
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
                                            \
        pe.audio.sys/THIS_IS*               \
        pe.audio.sys/.state                 \
        pe.audio.sys/config                 \
        pe.audio.sys/loudspeakers           \
        pe.audio.sys/macros                 \
        pe.audio.sys/share/eq/*target*      \
        bin/*                               \
        .mpdconf                            \
        .mplayer                            \
        .asoundrc                           \
        .profile                            \
        .crontab.dump                       \
        .config/xmgc                        \
        /etc/rc.local                       \
        /etc/fstab

    echo -n "(peaudiosys_backup.sh) "
    ls -sh "$tarpath"

}


function do_restore {

    # arguments $n are passed when calling the function,
    # and they have function scope.

    if [[ -f "$1" ]]; then
        tar_file="$1"
    else
        tar_file=$(ls -1 tmp/peaudiosys.bak_* | sort | tail -n1)
        echo "Using: ""$tar_file"
    fi


    cd
    if [[ -f "$tar_file" ]]; then
        read -r -p "Want to restore from: ""$tar_file"" (y/N) ? " ans
        if [ "$ans" != "y" ] && [ "$ans" != "Y" ]; then
            echo 'Ok, nothing done. Bye.'
            exit 0
        fi
        read -r -p "Are you sure to overwrite ~/pe.audio.sys, ~/bin (y/N) ? " ans
        if [ "$ans" != "y" ] && [ "$ans" != "Y" ]; then
            echo 'Ok, nothing done. Bye.'
            exit 0
        fi

        echo "Extracting ""$tar_file"" ... .. ."
        if tar -x -j -v -f $tar_file -C $HOME; then
            echo "Done."
            exit 0
        else
            echo "Error extracting tar file"
            exit 1
        fi

    else
        echo "error with ""$tar_file"
        exit 1
    fi
}


if [[ $1 == *"-b"* ]]; then
    do_backup

elif [[ $1 == *"-r"* ]]; then
    do_restore $2
else
    print_help
fi
