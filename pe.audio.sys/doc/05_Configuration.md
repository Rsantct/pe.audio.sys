# A check list to prepare your system 

Before turn on your amp, here we propose some check points to help you to prepare your pe.audio.sys to be ready to work.


## [  ] The `config.yml` file

Take the given `config.yml.sample` as a guide for your custom config.

Main points to check for:

    [ ] system_card: hw:ALSANAME
    
    [ ] jack_backend_options: -r SAMPLERATE -p PERIODSIZE -n PERIODS [--shorts] [--softmode]

        To initial testing, you can select here the dummy sound backend, with a channels dimension like your actual sound card.

    [ ] loudspeaker: YOUR_LOUDSPEAKER


## [  ] sound card's mixer setting

It is suggested to prepare `.asound.XXXX` files to ensure your sound card's mixer settings

More help running **`pe.audio.sys/share/scripts/sound_cards_prepare.py -h`**


## [  ] Loudspeaker folder

Review the README.md for **naming conventions and files under your loudspaker folder**.

### The `brutefir_config` file

You can begin from one of the provided loudspeaker examples as a template for customizing your `brutefir_config` file.

Also, we provide a tool **`peaudiosys_make_brutefir_config.py`** to prepare it for you by scanning the `.pcm` files under your loudspeaker folder. 

Please check:

    [  ] sampling_rate
    
    [  ] Tune properly the convolver's partition size, depending on your CPU available power, e.g.:
    
            filter_length:      16384 ;     # not partitioned
                    
            filter_length:      4096,4 ;    # 4 partitions, more CPU is needed.

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


For safety purposes, keep the initial 50.0 dB attenuation on `filter "f.lev.L"` and `filter "f.lev.R"` stages.

Once your `brutefir_config` file is ready, you can test it:


- Run Jack with a dummy backend:

        jackd -d dummy -P8 -C2 -r44100 &  # 8+2 channels

- Run Brutefir
    
        cd pe.audio.sys/loudspeakers/YOURLOUDSPEAKERFOLDER
        brutefir brutefir_config &.                         # (!) this 1st time will take a while

- Check Brutefir running process:

        bin/peaudiosys_view_brutefir.py



## [  ] EQ folder

You need to copy here ONE of the providided `share/eq/eq.sample.XX` subfolders set of files.

As a starting point, you may want to check the **full_range_example** loudspeaker, so copy all files from  `eq.sample.R20_audiotools`, because of curves compatibility:

    cd ~/pe.audio.sys/share/eq
    cp eq.sample.R20_audiotools/* . 


## [  ] The `.state.yml` file

Use the distro `.state.yml.sample`
     

## [  ] Environment variables

(i) If you comes from pre.di.c or FIRtro, please remove any `pre.di.c` directory reference from your `$PYTHONPATH` and `$PATH` environment variables under your `.profile`.

Then relogin.


## [ ] 1st time start up the system

Be sure you have set the DUMMY backend for jack, then run in backgound:

  **`pe.audio.sys/start.py all &`**

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
    su -l YourUser -c "python3 /home/YourUser/pe.audio.sys/start.py all --log &"
    exit 0

NOTICE: **`start.log`** will help you to debug the starting process.

## [ ] Restarting script

You may want to restart the whole `pe.audio.sys` system without console printouts. If so please consider the provided `bin/peaudiosys_restart.sh` script.
