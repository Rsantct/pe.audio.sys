# A check list to prepare your system 

Before turn on your amp, here we propose some check points to help you to prepare your pe.audio.sys to be ready to work.


## [  ] The `config.yml` file

Take the given `config.yml.example` as a guide for your custom config.

Use here the dummy sound backend, with the proper channels dimension, like your actual sound card.


## [  ] sound card's mixer setting

It is suggested to prepare `.asound.XXXX` files to ensure your sound card's mixer settings

More help running **`pe.audio.sys/share/scripts/sound_cards_prepare.py -h`**


## [  ] Loudspeaker folder

Review the README.md for **naming conventions and files under your loudspaker folder**.

### The `brutefir_config` file

You can begin from one of the provided loudspeaker examples as a template for customizing your `brutefir_config` file.

    [  ] Sound card out channels map
    
    [  ] output dither
    
    [  ] output delays
    
    [  ] coeffs definition, use relative path at the 'filename:' field (just the pcm filename)

        [  ] Declare coeffs for DRC

        [  ] Declare coeffs for XOVER (if a multiway speaker is used)

             For clarity and management reasons, both drc an xover coeff names
             MUST be the same as the pcm file w/o the .pcm extension


    [  ] filter stages (xover filtering and routing)
    
        [  ] Check carefully 'to_outputs': the polarity and attenuation you need on each way.

    [  ] WARNING: set a 50 dB atten for a SAFE STARTUP LEVEL:
           
            filter "f.drc.L" {
                from_filters: "f.eq.L"/50.0;
            ... ...
            filter "f.drc.R" {
                from_filters: "f.eq.R"/50.0;


Once your `brutefir_config` file is ready, you can test it:


- Run Jack with a dummy backend:

        jackd -d dummy -P8 -C2 -r44100 &  # 8+2 channels

- Run Brutefir
    
        cd pe.audio.sys/loudspeakers/YOURLOUDSPEAKERFOLDER
        brutefir brutefir_config &

- Check Brutefir running process:

        bin/peaudiosys_view_brutefir.py



## [  ] EQ folder

Nothing is needed here, the distro have an extensive set of 'target' eq files to start with.


## [  ] The `.state.yml` file

Use the distro `.state.yml.sample`
     

## [  ] Environment variables

(i) If you comes from pre.di.c or FIRtro, please remove any `pre.di.c` directory reference from your `$PYTHONPATH` and `$PATH` environment variables under your `.profile`.

Then relogin.


## [ ] 1st time start up the system

Be sure you have set the DUMMY backend for jack, then run:

  **`pe.audio.sys/start.py all`**

The provided tool `bin/peaudiosys_view_brutefir.py` will help you on mapping outputs, delays, coeefs, filters running, polarity and gains.

When things seems to be ok, you can try to use the actual alsa sound card, but **still keep your AMP switched off**:

- Set the ALSA backend at `config.yml`

- **`pe.audio.sys/start.py stop`**

- **`pe.audio.sys/start.py all`**

## [ ] Autorun on power on

On Debian systems, you can simply add a line inside your `/etc/rc.local` before `exit 0`

    #!/bin/sh -e
    ...
    ...
    su -l YourUser -c "python3 /home/YourUser/pe.audio.sys/start.py all >/home/YourUser/pe.audio.sys/start.py.log 2>&1"
    exit 0

NOTICE: **`start.py.log`** will help you to debug the starting process.

## [ ] Restarting scripts

You may want to prepare some script to restart the whole `pe.audio.sys`, if so please consider as below:

    #!/bin/bash

    # Failed to connect to session bus for device reservation: Unable to autolaunch a dbus-daemon without a
    # $DISPLAY for X11
    #
    # To bypass device reservation via session bus, set JACK_NO_AUDIO_RESERVATION=1 prior to starting jackd.
    #
    # Audio device hw:RPiCirrus,0 cannot be acquired...
    # Cannot initialize driver

    export JACK_NO_AUDIO_RESERVATION=1

    python3 /home/YourUser/pe.audio.sys/start.py all  \
    1>/home/YourUser/pe.audio.sys/start.py.log \
    2>&1 &






