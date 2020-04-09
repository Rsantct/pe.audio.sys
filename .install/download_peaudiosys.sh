#!/bin/bash

if [ -z $1 ] ; then
    echo usage:
    echo "    download_peaudiosys.sh  branch_name [git_repo]"
    echo
    exit 0
fi
branch=$1

if [ $2 ]; then
    gitsite="https://github.com/""$2"
else
    gitsite="https://github.com/Rsantct"
fi

echo
echo "WARNING: Will download from: [ ""$gitsite"" ]"
read -r -p "         Is this OK? [y/N] " tmp
if [ "$tmp" != "y" ] && [ "$tmp" != "Y" ]; then
    echo 'Bye.'
    exit 0
fi


# Prepare temp directory
mkdir $HOME/tmp > /dev/null 2>&1
cd $HOME/tmp

# Removes any existent master.zip or predic directory for this branch:
rm $branch.zip
rm -r pe.audio.sys-$branch

# Downloads the zip
wget "$gitsite"/pe.audio.sys/archive/"$branch".zip

# Unzip
unzip $branch.zip
rm $branch.zip

# Drops the installing (download and update) scripts into tmp/ to be accesible
cp -f pe.audio.sys-$branch/.install/*sh .

# And back to home
cd
rm download_peaudiosys.sh > /dev/null 2>&1
