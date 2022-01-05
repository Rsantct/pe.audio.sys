#!/bin/sh

# (i) NOTICE:   When maintaining this script, do NOT edit it directly
#               from ~/tmp/ because it will be modified on runtime.
#               So edit it apart, copy to ~/tmp/ and test it.

if [ -z $1 ] ; then
    echo usage by indicating a previously downloaded branch in tmp/
    echo "    download_peaudiosys.sh master|testing|xxx"
    echo
    exit 0
fi

# --auto for unattended maintenance
if [ $1 = "--auto" ]; then
    automode=1
    branch="master"
else
    automode=0
    branch=$1
fi


ORIG=$HOME/tmp/pe.audio.sys-$branch
# If not found the requested branch
if [ ! -d $ORIG ]; then
    echo
    echo ERROR: not found $ORIG
    echo must indicate a branch name suffix as available at ~/tmp/pe.audio.sys-xxx:
    echo "    update_peaudiosys.sh master|testing|xxx"
    echo
    exit 0
fi


keepConfig="1"

if [ $automode -eq 0 ]; then

    # Wanna keep current configurations?
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

fi


########################################################################
# BACK UP USER CONFIG FILES
########################################################################

# ALSA .asoundrc is distributed as a .sample file and not updated here.

# MPLAYER
cd "$HOME"/.mplayer
cp config           config.LAST             >/dev/null 2>&1
cp channels.conf    channels.conf.LAST      >/dev/null 2>&1
echo "(i) backing up .mplayer files"

# MPD:
cd "$HOME"
cp .mpdconf .mpdconf.LAST

# PE.AUDIO.SYS:
# use .LAST instead of .bak in order to respect any existing bak file if so.
if [ -d "pe.audio.sys" ]; then
    echo "(i) backing up pe.audio.sys config files"
    for file in pe.audio.sys/config/*.yml ; do
        cp "$file" "$file.LAST"
    done
fi

# WWW: does not contain any configurable file

########################################################################
# CLEANING OLDIES
########################################################################
cd "$HOME"
if [ -d "pe.audio.sys" ]; then
    echo "(i) Removing old distro files"
    rm -rf  pe.audio.sys/doc/               >/dev/null 2>&1
    rm      pe.audio.sys/*BRANCH            >/dev/null 2>&1

    # major updates moved some files, so let's clean them all
    rm -rf  pe.audio.sys/share/services     >/dev/null 2>&1
    rm -rf  pe.audio.sys/share/miscel_mod   >/dev/null 2>&1
    rm -rf  pe.audio.sys/share/www          >/dev/null 2>&1
    rm      pe.audio.sys/share/*            >/dev/null 2>&1
fi

########################################################################
# COPYING THE NEW STUFF
########################################################################
echo "(i) Copying from $ORIG ..."
cd "$HOME"
# HIDDEN FILES (!) must explicit each one so they can be copied
cp    $ORIG/.asoundrc.sample    $HOME/              >/dev/null 2>&1
# MPLAYER
cp -r $ORIG/.mplayer*           $HOME/              >/dev/null 2>&1
# MPD
mkdir -p $HOME/music
mkdir -p $HOME/.config/mpd/playlists
cp    $ORIG/.mpdconf.sample     $HOME/              >/dev/null 2>&1
# MAIN
mkdir -p $HOME/pe.audio.sys/config
mkdir -p $HOME/pe.audio.sys/log
cp -r $ORIG/pe.audio.sys/       $HOME/              >/dev/null 2>&1
# SOME UTILS are provided inside ~/bin
mkdir -p $HOME/bin
cp    $ORIG/bin/*               $HOME/bin/          >/dev/null 2>&1

########################################################################
# RESTORING PREVIOUS CONFIG IF DESIRED
########################################################################
if [ "$keepConfig" ]; then

    # MPLAYER
    cd "$HOME"/.mplayer
    mv config.LAST          config
    mv channels.conf.LAST   channels.conf
    echo "(i) Restoring .mplayer config files"

    # MPD
    cd "$HOME"
    mv .mpdconf.LAST        .mpdconf

    # PE.AUDIO.SYS
    echo "(i) Restoring pe.audio.sys config files"
    cd "$HOME"/pe.audio.sys/config
    for file in *yml.LAST ; do
        nfile=${file%.LAST}         # removes trailing .LAST '%'
        echo "    "$nfile
        mv $file $nfile
    done

########################################################################
# If NO KEEPING CONFIG, then overwrite:
########################################################################
else

    # MPLAYER
    cd "$HOME"/.mplayer
    cp config.sample            config
    cp channels.conf.sample     channels.conf
    echo "(i) .mplayer files has been updated"

    # MPD
    cd "$HOME"
    cp .mpdconf.sample          .mpdconf
    echo "(i) .mpdconf has been updated"

    # MAIN
    cd "$HOME"/pe.audio.sys
    cp .state.sample             .state
    cd "$HOME"/pe.audio.sys/config
    cp config.yml.sample         config.yml
    cp DVB-T.yml.sample          DVB-T.yml        >/dev/null 2>&1
    cp istreams.yml.sample       istreams.yml     >/dev/null 2>&1

    echo "(i) New config.yml and .state files NEEDS to be adapted"
fi

########################################################################
# Restoring exec permissions
########################################################################
cd "$HOME"
chmod +x    pe.audio.sys/start.py                   >/dev/null 2>&1
chmod +x    pe.audio.sys/pasysctrl                  >/dev/null 2>&1
chmod +x    pe.audio.sys/macros/*                   >/dev/null 2>&1
chmod +x    pe.audio.sys/macros/examples/*          >/dev/null 2>&1
chmod -x    pe.audio.sys/macros/*.md                >/dev/null 2>&1
chmod -R +x pe.audio.sys/share/scripts/*            >/dev/null 2>&1
chmod +x    pe.audio.sys/share/services/server.py   >/dev/null 2>&1
chmod +x    pe.audio.sys/share/services/preamp_mod/jloops_daemon.py \
                                                    >/dev/null 2>&1
chmod +x    bin/*py                                 >/dev/null 2>&1
chmod +x    bin/peaudiosys*                         >/dev/null 2>&1

########################################################################
# Prepare miscel files
########################################################################
mkfifo pe.audio.sys/.cdda_fifo               >/dev/null 2>&1
mkfifo pe.audio.sys/.dvb_fifo                >/dev/null 2>&1
mkfifo pe.audio.sys/.istreams_fifo           >/dev/null 2>&1
touch pe.audio.sys/.cdda_events
touch pe.audio.sys/.dvb_events
touch pe.audio.sys/.istreams_events
touch pe.audio.sys/.librespot_events
touch pe.audio.sys/.mpd_events
touch pe.audio.sys/.playerctl_spotify_events
touch pe.audio.sys/.spotify_events

########################################################################
# A helping file to identify the current branch
########################################################################
touch pe.audio.sys/THIS_IS_"$branch"_BRANCH
echo "as per update_peaudiosys.sh" > pe.audio.sys/THIS_IS_"$branch"_BRANCH
echo ""
echo "(i) Done."
echo ""

########################################################################
# Symlink to use the SOCKET version of server.py (can change in a future)
########################################################################
ln -s $HOME/pe.audio.sys/share/miscel/server.py.SOCKET \
      $HOME/pe.audio.sys/share/miscel/server.py         1>/dev/null 2>&1


########################################################################
# Restore drc png files under www/images
########################################################################
python3 pe.audio.sys/share/www/scripts/drc2png.py 1>/dev/null 2>&1 &


########################################################################
# Finally updates the updater script under ~/tmp/
########################################################################
cp "$ORIG"/.install/update_peaudiosys.sh "$HOME"/tmp/

########################################################################
# AUTOUPDATE MODE
########################################################################
if [ $automode -eq 1 ]; then
    # Mofifies the user crontab with daily updates if auto_update is configured
    sauc="$HOME/tmp/pe.audio.sys-master/.install/crontab/set_auto_update_cronjob.sh"
    if [ -e $sauc ]; then
        sh $sauc
    fi
    $HOME/bin/peaudiosys_server_restart.sh
    echo "END of automatic update, bye!"
    exit 0
fi

########################################################################
# END
########################################################################



########################################################################
#                            WEB SITE
########################################################################

########################################################################
# clientside.js needs to be adapted depending on you using
# Apache or Node.js as your pe.audio.sys http server
########################################################################
a2ensites=$(ls /etc/apache2/sites-enabled/)

# normal web site
forig_www=$ORIG"/.install/apache-site/pe.audio.sys.conf"
fdest_www="/etc/apache2/sites-available/pe.audio.sys.conf"

# optional web site with wakeonlan site
forig_wol=$ORIG"/.install/apache-site/pe.audio.sys_wol.conf"
fdest_wol="/etc/apache2/sites-available/pe.audio.sys_wol.conf"

# updating HOME path inside xxx.conf files
sed -i s/paudio/$(basename $HOME)/g  $forig_www
sed -i s/paudio/$(basename $HOME)/g  $forig_wol


# Using Apache
if test "${a2ensites#*pe.audio.sys}" != "$a2ensites"; then
    echo "(i) Will configure www/clientside.js for Apache server"
    echo
    echo "(i) Checking the website 'pe.audio.sys'"
    echo "    /etc/apache2/sites-available/pe.audio.sys.conf"
    echo
    updateWeb=1
    if [ -f $fdest_www ]; then
        if ! cmp --quiet $forig_www $fdest_www; then
            echo "(i) A new version is available "
            echo "    "$forig_www"\n"
        else
            echo "(i) No changes on the website\n"
            updateWeb=""
        fi
    fi
    if [ "$updateWeb" ]; then
        echo "(!) You need admin privilegies (sudo)"
        echo "( ^C to cancel the website update )\n"
        # normal web site
        sudo cp $forig_www $fdest_www
        # prepare optional wakeonlan site
        sudo cp $forig_wol $fdest_wol
        # disable default Apache site
        sudo a2dissite 000-default.conf
        # a helper when migrating from pre.di.c
        sudo a2dissite pre.di.c.conf
        # enable normal site
        sudo a2ensite pe.audio.sys.conf
        sudo service apache2 reload
    fi

# Using Node.js
else
    echo "(i) Will configure www/clientside.js for Node.js server"
    sed -i -e "/const\ URL_PREFIX/c\const\ URL_PREFIX\ =\ \'\/\';" \
           "${HOME}"/pe.audio.sys/share/www/clientside.js
fi
