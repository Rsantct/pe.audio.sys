#!/bin/bash

function print_help {
    echo
    echo "    A tool to backup or restore pe.audio.sys files to/from"
    echo "        tmp/peaudiosys.bak_xxxxxxx"
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

    now=$(date +%Y%m%d.%H%M%S)

    tar --exclude=*.wav             \
        --exclude=*.dat             \
        --exclude=*.png             \
        --exclude=*.pcm             \
        --exclude=*config/asound*   \
        --exclude=*loudspeakers/*example*   \
        --exclude=*loudspeakers/*test*      \
        --exclude=*/www/images/*    \
        --exclude=*.pyc             \
        --exclude=*__pycache__*     \
        --exclude=*share/eq*        \
        --exclude=*.sample*         \
        -cjf $HOME/tmp/peaudiosys.bak_"$now".tar.bz2    \
            pe.audio.sys/start.py               \
            pe.audio.sys/config                 \
            pe.audio.sys/loudspeakers           \
            pe.audio.sys/macros                 \
            pe.audio.sys/share/audiotools       \
            pe.audio.sys/share/miscel           \
            pe.audio.sys/share/scripts          \
            pe.audio.sys/share/services         \
            pe.audio.sys/share/www              \
            bin/peaudiosys*

    ls -sh tmp/peaudiosys.bak_"$now".tar.bz2

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
        if tar -xjf $tar_file -C $HOME; then
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
