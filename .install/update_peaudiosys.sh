#!/bin/bash

if [ -z $1 ] ; then
    echo usage by indicating a previously downloaded branch in tmp/
    echo "    download_peaudiosys.sh master|testing|xxx"
    echo
    exit 0
fi

branch=$1
DEST=$HOME
ORIG=$DEST/tmp/pe.audio.sys-$branch

# If not found the requested branch
if [ ! -d $ORIG ]; then
    echo
    echo ERROR: not found $ORIG
    echo must indicated a branch name available at ~/tmp/pe.audio.sys-xxx:
    echo "    update_peaudiosys.sh master|testing|xxx"
    echo
    exit 0
fi

# Wanna keep current configurations?
keepConfig="1"
read -r -p "WARNING: will you keep current config? [Y/n] " tmp
if [ "$tmp" = "n" ] || [ "$tmp" = "N" ]; then
    echo All files will be overwritten.
    read -r -p "Are you sure? [y/N] " tmp
    if [ "$tmp" = "y" ] || [ "$tmp" = "Y" ]; then
        keepConfig=""
    else
        keepConfig="1"
        echo Will keep current config.
    fi
fi

read -r -p "WARNING: continue updating? [y/N] " tmp
if [ "$tmp" != "y" ] && [ "$tmp" != "Y" ]; then
    echo Bye.
    exit 0
fi

#########################################################
# BACK UP
#########################################################

cd "$DEST"

echo "(i) backing up user home folder config files"

# HOME:
cp .asoundrc                .asoundrc.LAST                >/dev/null 2>&1
cp .mpdconf                 .mpdconf.LAST                 >/dev/null 2>&1

# MPLAYER
cp .mplayer/config          .mplayer/config.LAST          >/dev/null 2>&1
cp .mplayer/channels.conf   .mplayer/channels.conf.LAST   >/dev/null 2>&1

# PE.AUDIO.SYS
echo "(i) backing up pe.audio.sys config files"
for file in pe.audio.sys/*.yml ; do
    cp "$file" "$file.LAST"
done

# WWW does not contains any configurable file

#########################################################
# CLEANING
#########################################################
echo "(i) Removing old files,"
echo "    but keeping the user maintained ones:"
echo "      - scripts/ except those from this distro"
echo "      - web buttons macros"

cd $HOME

# remove old files
rm -r   pe.audio.sys/doc/               >/dev/null 2>&1
rm      pe.audio.sys/share/*            >/dev/null 2>&1
rm      pe.audio.sys/www/index.html     >/dev/null 2>&1
rm -rf  pe.audio.sys/www/php            >/dev/null 2>&1
rm -rf  pe.audio.sys/www/js             >/dev/null 2>&1

#########################################################
# COPYING THE NEW STUFF
#########################################################
echo "(i) Copying from $ORIG to $DEST"
cp -r $ORIG/*             $DEST/
# hidden files must be explicited each one to be copied
cp    $ORIG/.mpdconf      $DEST/           >/dev/null 2>&1
cp -r $ORIG/.mplayer*     $DEST/           >/dev/null 2>&1

#########################################################
# RESTORING PREVIOUS CONFIG IF DESIRED
#########################################################
if [ "$keepConfig" ]; then

    cd $HOME

    echo "(i) Restoring user home config files"

    echo "    ".asoundrc
    mv .asoundrc.LAST               .asoundrc               >/dev/null 2>&1

    echo "    ".mpdconf
    mv .mpdconf.LAST                .mpdconf                >/dev/null 2>&1

    echo "    ".mplayer/config
    mv .mplayer/config.LAST         .mplayer/config         >/dev/null 2>&1
 
    echo "    ".mplayer/channels.conf
    mv .mplayer/channels.conf.LAST  .mplayer/channels.conf  >/dev/null 2>&1

    echo "(i) Restoring pe.audio.sys config files"
    cd "$HOME"pe.audio.sys
    for file in *yml.LAST ; do
        nfile=${file%.LAST}         # removes trailing .LAST '%'
        echo "    "$nfile
        mv $file $nfile
    done
    
########################################################################
# If NO KEEPING CONFIG, then overwrite:
########################################################################
else
    cd "$HOME"pe.audio.sys

    cp .state.yml.sample         .state.yml
    cp config.yml.example        config.yml
    cp DVB-T.yml.sample          DVB-T.yml        >/dev/null 2>&1
    cp istreams.yml.sample       istreams.yml     >/dev/null 2>&1
    echo "(i) New config.yml and .state files NEED to be adapted"
fi


cd "$HOME"

#########################################################
# Restoring FIFOs
#########################################################
echo "(i) Making fifos for mplayer services"
rm -f  pe.audio.sys/.*fifo
mkfifo pe.audio.sys/.dvb_fifo         # DVB-T
mkfifo pe.audio.sys/.cdda_fifo        # CDDA
mkfifo pe.audio.sys/.istreams_fifo    # internet streams

#########################################################
# Restoring exec permissions
#########################################################

chmod -x -R pe.audio.sys/*                  >/dev/null 2>&1
chmod +x -R pe.audio.sys/*.py               >/dev/null 2>&1
chmod +x    pe.audio.sys/macros/*           >/dev/null 2>&1
chmod -x    pe.audio.sys/macros/*.md        >/dev/null 2>&1
chmod +x    pe.audio.sys/share/scripts/*    >/dev/null 2>&1
chmod +x    pe.audio.sys/share/server.py    >/dev/null 2>&1

#########################################################
# A helping file to identify the current branch
#########################################################
touch pe.audio.sys/THIS_IS_"$branch"_BRANCH
echo "as per update_peaudiosys.sh" > pe.audio.sys/THIS_IS_"$branch"_BRANCH
echo ""
echo "(i) Done."
echo ""

#########################################################
# And updates the updater script
#########################################################
cp "$ORIG"/.install/update_peaudiosys.sh "$DEST"/tmp/

#########################################################
# END
#########################################################


#########################################################
# Apache site
#########################################################
forig=$ORIG"/.install/apache-site/pe.audio.sys.conf"
fdest="/etc/apache2/sites-available/pe.audio.sys.conf"
updateWeb=1
echo ""
echo "(i) Checking the website 'pe.audio.sys'"
echo "    /etc/apache2/sites-available/pe.audio.sys.conf"
echo ""

if [ -f $fdest ]; then
    if ! cmp --quiet $forig $fdest; then
        echo "(i) A new version is available "
        echo "    "$forig"\n"
    else
        echo "(i) No changes on the website\n"
        updateWeb=""
    fi
fi
if [ "$updateWeb" ]; then
    echo "(!) You need admin privilegies (sudo)"
    echo "(i) ... or maybe you don't want to update pe.audio.sys.conf"
    echo "        because your home dir is not /home/peaudiosys"
    echo "( ^C to cancel the website update )\n"
    sudo cp $forig $fdest
    sudo a2ensite pre.di.c.conf
    sudo a2dissite 000-default.conf
    sudo service apache2 reload
fi
echo ""
echo "(i) NOTICE:"
echo "    If you install pe.audio.sys under a home other than '/home/peaudiosys'"
echo "    please update accordingly:"
echo "        ""$fdest"
