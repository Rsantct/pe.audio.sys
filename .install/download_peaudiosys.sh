#!/bin/sh

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

if [ -z $1 ] ; then
    echo "usage:"
    echo "    download_peaudiosys.sh  branch_name [git_repo]"
    echo
    echo "    (i) optional git_repo defaults to 'AudioHumLab'"
    echo
    exit 0
fi

if [ $2 ]; then
    gitsite="https://github.com/""$2"
else
    gitsite="https://github.com/AudioHumLab"
fi

# --auto unattended maintenance
if [ $1 = "--auto" ]; then
    automode=1
    gitsite="https://github.com/AudioHumLab"
    branch="master"
else
    automode=0
    branch=$1
fi

if [ $automode -eq 0 ]; then
    echo
    echo "WARNING: Will download from: ""$gitsite""/""$branch"
    read -r -p "         Is this OK? [y/N] " tmp
    if [ "$tmp" != "y" ] && [ "$tmp" != "Y" ]; then
        echo 'Bye.'
        exit 0
    fi
fi

mkdir $HOME/tmp > /dev/null 2>&1

cd $HOME/tmp

# delete if any previous zip here, then download and unzip
rm -f $branch.zip
echo "Please wait while downloading ... .. ."
if ! wget --no-verbose "$gitsite"/pe.audio.sys/archive/"$branch".zip; then
    echo "error downloading fron github"
    exit 1
fi
rm -rf pe.audio.sys-$branch
echo "Please wait while unzipping ... .. ."
if ! unzip -q $branch.zip; then
    echo "error with zip file"
    exit 1
fi

# Special file containing the unique zip comment,
# in order to check if updates are needed.
unzip -z $branch.zip > pe.audio.sys-"$branch"/pe.audio.sys/THIS_IS_"$branch"_BRANCH

rm -f $branch.zip

cp -f pe.audio.sys-$branch/.install/download_peaudiosys.sh .
cp -f pe.audio.sys-$branch/.install/update_peaudiosys.sh   .

cd
rm -f download_peaudiosys.sh

echo "Done."
