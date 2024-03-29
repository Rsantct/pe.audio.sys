## Jackd fails to start because the sound card is in use.

### Check for any jackd session running on your system:

    $ pgrep -fla jackd

### Check for services using your sound card.

It is known in some scenarios, for instance after a Debian/Raspbian/Ubuntu distro upgrade, there can be some system service that uses the sound card:

    $ sudo fuser -v /dev/snd/*
                         USER        PID ACCESS COMMAND
    /dev/snd/controlC0:  root        292 f.... alsactl
    /dev/snd/pcmC0D0p:   timidity    573 F.... timidity
    /dev/snd/seq:        timidity    573 F.... timidity

Some users reported the ALSA card was weirdly used by Pulseaudio instead of Timidity:

    $ sudo fuser -v /dev/snd/*
                         USER        PID ACCESS COMMAND
    /dev/snd/controlC0:  root       1234 f.... pulseaudio

But this is still a Timidity issue even if `pulseaudio` is indicated by `fuser`.

Timidity is a sound synthesizer, we don't need it at all, so let's disable it:

    $ sudo systemctl stop timidity.service
    $ sudo systemctl disable timidity.service


## Web page does not work.

### Apache http server:

Be sure the Apache's PHP module is installed and enabled:

    $ sudo apt install apache2 libapache2-mod-php
    $ ls /etc/apache2/mods-available/php*
    /etc/apache2/mods-available/php7.3.conf
    /etc/apache2/mods-available/php7.3.load
    $ sudo a2enmod php7.3


    $ ls /etc/apache2/sites-enabled/
    000-default.conf  pe.audio.sys.conf

If enabled, disable default Apache site:
    
    $ sudo a2dissite 000-default.conf
    Site 000-default disabled.
    To activate the new configuration, you need to run:
      systemctl reload apache2

Reload Apache

    $ sudo systemctl reload apache2
    

## Which Spotify client to use?

### Desktop

If you run a desktop system with enough CPU, your friend is the official Spotify package for Linux https://www.spotify.com/en/download/linux/

This is the preferred because pe.audio.sys will obtain complete metatada info.

### Headless

If you want a headless system, your friend is **`librespot`** https://github.com/librespot-org/librespot

Please see [80_Spotify_connect.md](https://github.com/Rsantct/pe.audio.sys/blob/wip/pe.audio.sys/doc/80_Spotify_connect.md#spotify-connect-client-aka-librespot)


## Can I run Brutefir compiled from source rather than my distro version

Yes. Simply download it from source, install and symlink the new binary under your $HOME/bin folder.

Example to install Brutefir 1.0o version (see latest at https://torger.se/anders/brutefir.html#download)

    sudo apt-get install build-essential flex libasound2-dev libjack-jackd2-dev libfftw3-dev
    mkdir ~/tmp
    cd tmp
    wget http://www.ludd.luth.se/~torger/files/brutefir-1.0o.tar.gz
    tar xvzf brutefir-1.0o.tar.gz
    cd brutefir-1.0o
    make
    sudo make install

The installed new files will be shown as:

    install -d /usr/local/bin /usr/local/lib/brutefir
    install brutefir /usr/local/bin
    install cli.bflogic eq.bflogic file.bfio alsa.bfio oss.bfio jack.bfio /usr/local/lib/brutefir

So now you can symlink it to run the new version:

    ln -s /usr/local/bin/brutefir $HOME/bin/brutefir



## About zita-j2n (JACK-NETWORK BRIDGE) network usage

https://kokkinizita.linuxaudio.org/linuxaudio/

For a typical setting of 2 ch 44100 Hz 16 bit, the used BW is about 1.7 Mb/s over your LAN.

If you use **`plugins/zita-n2j_mcast.py`**, then UDP multicast packets will be sent continously to ALL hosts in your LAN.

Please USE MULTICAST ONLY in a dedicated wired Ethernet LAN.

If you have a **WiFied LAN, do not use multicast**. Maybe you can use the integrated one-to-one zita-njbridge. See **`doc/Multiroom`**


## How to tune DVB-T channels

    sudo apt-get install dvb-apps w-scan
    w_scan -ft -cES -M > ~/.mplayer/channels.conf # see notes below

w_scan notes:

    X = czap/tzap/xine channels.conf
    x = "initial tuning data" for Scan
    G = Gstreamer dvbsrc Plugin
    k = channels.dvb for Kaffeine
    L = VLC xspf playlist (experimental)
    M = mplayer format, similar to X

More info here: https://github.com/AudioHumLab/FIRtro/wiki/815-DVB-T-Radio-(TDT)-con-mplayer

More technical info: http://linuxtv.org/wiki/index.php/W_scan


## About Bluetooth sources

Please refer to **`doc/80_Bluetooth.md`**.


## Desktop session autologin

Only recommended if you want to run an Spotify desktop client at startup. To enable it in Debian.

    /etc/gdm3/daemon.conf
        ...
        ...
        AutomaticLoginEnable = true
        AutomaticLogin = paudio
        ...
        ...

(!) If so, please consider REMOVE **`paudio`** from your machine **`sudo`** group.


## How can I switch my amplifier?

You can use a commercial `sispmctl` compatible USB controlled power strip.

Also, you can home made your own USB controlled power socket, for instance by using some cheap `usbrelay` compatible relay board, more info inside the provided `bin/amp_on_off.py_usbrelay.example`.

You need to prepare a custom script to manage the power socket:

- The script must accept `on|off` as argument
- The script must keep a file `~/.amplifier` containing `on` `1` `off` `0` as per the power socket status.

Then declare it inside `config.yml`, for instance:

    amp_manager:   ~/bin/amp_on_off.py

This way `pe.audio.sys` will control the amp power outlet, as well will notice the power outlet state changes.


## How to convert the former state file to json format

If you need to migrate your old system, you can run the following:

    $ nano bin/state2json.py

        #!/usr/bin/env python3
        import json
        import yaml
        with open('pe.audio.sys/.state.yml', 'r') as f:
            state = yaml.safe_load( f.read() )
        with open('pe.audio.sys/.state', 'w') as f:
            f.write( json.dumps(state) )

    $ python3 bin/state2json

Once updated your pe.audio.sys, you can safely delete old `.yml` files:

    $ rm pe.audio.sys/.state.yml*




