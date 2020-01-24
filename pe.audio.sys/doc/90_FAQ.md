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

## Web page does not works.

### Apache http server:

Be sure the Apache's PHP module is installed and enabled:

    $ sudo apt install apache2 libapache2-mod-php
    $ ls /etc/apache2/mods-available/php*
    /etc/apache2/mods-available/php7.3.conf
    /etc/apache2/mods-available/php7.3.load
    $ sudo a2enmod php7.3

