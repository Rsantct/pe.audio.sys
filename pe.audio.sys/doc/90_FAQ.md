## Jackd fails to start because the sound card is in use.

### Check for any jackd session running on your system:

    $ pgrep -fla jackd

### Check for services using your sound card.

It is known in some scenarios, for instance after a raspbian upgrading distro, there can be some system service that uses the sound card:

    $ sudo fuser -v /dev/snd/*
                         USER        PID ACCESS COMMAND
    /dev/snd/controlC0:  root        292 f.... alsactl
    /dev/snd/pcmC0D0p:   timidity    573 F.... timidity
    /dev/snd/seq:        timidity    573 F.... timidity

Timidity is a sound synthesizer, we don't need it at all:

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

## Which Spotify client to use?

### Desktop

If you run a desktop system with enough CPU, your friend is the official Spotify package for Linux https://www.spotify.com/en/download/linux/

This is the preferred because pe.audio.sys will obtain complete metatada info.

### Headless

If you want a headless system, your friend is **`librespot`** https://github.com/librespot-org/librespot

`librespot` is provided as a package from the [Rust ecosystem](https://crates.io/crates/librespot), so you'll need simply to install `cargo`, the Rust package manager, then install `librespot`:

    sudo apt install cargo
    cargo install librespot  # This will take a long while to compile
    
Don't worry about the --backend option because by default will use Rodio that works as kind of intermediate to use ALSA or Coreaudio, as needed.

Unfortunately, librestpot only provides the current song title, nor artist neither album info.
    
 #### Raspberry Pi
 
 There is available a pre-compiled package for arm Raspberry users: raspotify https://github.com/dtcooper/raspotify

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

For a typical setting of 2 ch 44100 Hz 16 bit, the used BW is about 1.7 Mb/s over your LAN.

If you use **`scripts/zita-n2j_mcast.py`**, then UDP multicast packets will be sent continously to ALL hosts in your LAN.

So, you can use MULTICAST only in a dedicated wired Ethernet LAN.

If you have a **WiFied LAN, do not use multicast**. It is preferred to use the new client side **`scripts/zita_link.py`**. This script automagically triggers the sender system to run a one-to-one `zita-j2n` process.


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

More info: http://linuxtv.org/wiki/index.php/W_scan

