## Jackd fails to start because the sound card is in use.

### Check for any jackd session runing on your system:

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
