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

### Headless

If you want a headless system, your friend is **`librespot`** https://github.com/librespot-org/librespot

`librespot` is provided as a package from the [Rust ecosystem](https://crates.io/crates/librespot), so you'll need simply to install `cargo`, the Rust package manager, then install `librespot`:

    sudo apt install cargo
    cargo install librespot  # This will take a long while to compile
    
Don't worry about the --backend option because by default will use Rodio that works as kind of intermediate to use ALSA, Pulseaudio, Coreaudio, as needed.
    
 #### Raspberry Pi
 
 There is available a pre-compiled package for arm Raspberry users: raspotify https://github.com/dtcooper/raspotify

## The control web page fails to display metadata info for CDs 

You need to install the **`cdcd`** tool, then run once from command line to configure it:

    $ sudo apt install cdcd
    $ cdcd      # an say 'y'
    
