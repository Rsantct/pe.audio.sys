#!/bin/bash

echo
read -p "Enter the GitHub site (intro to 'AudioHumLab'): " ans
if [[ ! $ans ]];then
    GITSITE="AudioHumLab"
else
    GITSITE=$ans
fi

echo
read -p "Enter the branch (intro to 'master'): " ans
if [[ ! $ans ]];then
    BRANCH="master"
else
    BRANCH=$ans
fi

echo
read -p "Upgrading from 'https://github.com/"$GITSITE"/"$BRANCH"'.  It's ok? (y/N): " ans
if [[ $ans != *"y"*  && $ans != *"Y"* ]];then
    echo 'Bye!'
    exit 0
fi


cd
mkdir -p ~/tmp
cd ~/tmp
mv download_peaudiosys.sh   download_peaudiosys.sh.OLD  1>/dev/null 2>&1
mv update_peaudiosys.sh     update_peaudiosys.sh.OLD    1>/dev/null 2>&1
wget --quiet --show-progress \
     https://raw.githubusercontent.com/$GITSITE/pe.audio.sys/$BRANCH/.install/download_peaudiosys.sh
wget --quiet --show-progress \
     https://raw.githubusercontent.com/$GITSITE/pe.audio.sys/$BRANCH/.install/update_peaudiosys.sh


cd

echo
echo "WE ARE ABOUT TO DOWNLOAD THE SOFTWARE ..."
sh ~/tmp/download_peaudiosys.sh $BRANCH $GITSITE

echo
echo "WE ARE ABOUT TO UPGRADE THE SOFTWARE ..."
sh ~/tmp/update_peaudiosys.sh $BRANCH --force

