## ACHTUNG:

First of all it is strongly recommended that your Linux distro has Python3 version >= 3.6,
so try to upgrade your Linux before continue.

## Your Linux enviroment and packages:

See here: 

https://github.com/AudioHumLab/FIRtro/wiki/04a-Instalación-de-Linux-y-paquetes-de-SW

Usually it is enough:

- add the **`peaudiosys`** user to your system, this is optional because you can run the **pe.audio.sys** system under **ANY USER ACCOUNT** if you want so.

    `sudo adduser peaudiosys`

- then integrate the user which will run pe.audio.sys into convenient groups:

    `sudo usermod -a -G cdrom,audio,video,plugdev YourUserHere`

Unlike `pre.di.c` **enviroment settings**, here it is no longer needed to point the PYTHONPATH environment variable to your `pe.audio.sys` directories.

Update your `~/.profile`:

    export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket


Enable your user to access the sound card under the dbus system enviroment:

    sudo nano /etc/dbus-1/system-local.conf
    
        <busconfig>
          <!-- pe.audio.sys -->
            <policy user="YourUserHere">
              <allow own="org.freedesktop.ReserveDevice1.Audio0"/>
              <allow own="org.freedesktop.ReserveDevice1.Audio1"/>
              <allow own="org.freedesktop.ReserveDevice1.Audio2"/>
              <allow own="org.freedesktop.ReserveDevice1.Audio3"/>
            </policy>
        </busconfig>
    
    
    sudo service dbus restart


Also install the following packages on your linux installation:

    sudo apt install alsa-utils libjack-jackd2-dev libasound2-dev libasound2-plugins
    sudo apt install jackd2 brutefir ecasound ecatools python-ecasound mpd mpc mplayer
    sudo apt install ladspa-sdk fil-plugins zita-ajbridge zita-njbridge apache2 libapache2-mod-php


### Python3 packages

Please refer to the doc files here
