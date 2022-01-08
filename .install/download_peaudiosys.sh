#!/bin/sh

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

# --auto for unattended maintenance
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
    echo "WARNING: Will download from: [ ""$gitsite"" ]"
    read -r -p "         Is this OK? [y/N] " tmp
    if [ "$tmp" != "y" ] && [ "$tmp" != "Y" ]; then
        echo 'Bye.'
        exit 0
    fi
fi

# Prepare temp directory
mkdir $HOME/tmp > /dev/null 2>&1
cd $HOME/tmp

# Removes any existent master.zip or predic directory for this branch:
rm -f $branch.zip
rm -rf pe.audio.sys-$branch

# Downloads the zip
echo "Please wait while downloading ... .. ."
if ! wget --no-verbose "$gitsite"/pe.audio.sys/archive/"$branch".zip; then
    exit 1
fi

# Unzip
echo "Please wait while unzipping ... .. ."
if ! unzip -q $branch.zip; then
    echo "error with zip file"
    exit 1
fi
unzip -z $branch.zip
rm -f $branch.zip

# Drops the installing (download and update) scripts into tmp/ to be accesible
cp -f pe.audio.sys-$branch/.install/download_peaudiosys.sh .
cp -f pe.audio.sys-$branch/.install/update_peaudiosys.sh   .

# And back to home
cd
rm -f download_peaudiosys.sh
