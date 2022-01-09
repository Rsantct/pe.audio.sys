#!/bin/bash

function print_help {
    echo "usage:   peaudiosys_backup.sh  -backup | -restore"
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
    cd
    last_tar=$(ls -1 tmp/peaudiosys.bak_* | sort | tail -n1)
    if [[ -f "$last_tar" ]]; then
        read -r -p "want to restore from: ""$last_tar"" (y/N) ? " ans
        if [ "$ans" != "y" ] && [ "$ans" != "Y" ]; then
            echo 'Ok, nothing done. Bye.'
            exit 0
        fi

        echo WIP

    else
        echo "error with ""$last_tar"
        exit 1
    fi
}


if [[ $1 == *"-b"* ]]; then
    do_backup

elif [[ $1 == *"-r"* ]]; then
    do_restore
else
    print_help
fi
