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

    [  ] sound card out channels map
    [  ] output dither
    [  ] output delays
    [  ] coeffs definition (*), use relative path just the pcm filename
        [  ] coeffs for DRC
        [  ] coeffs for XOVER (if a multiway speaker is used)

    [  ] filter stages (*)
        [  ] check carefully 'to_outputs': the polarity and attenuation you need on each way.

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

(i) If you comes from pre.di.c or FIRtro, please remove any pre.dic.c directory from your $PYTHONPATH environment variable under your `.profile`


## [ ] 1st time start up the system

Be sure you have set the DUMMY backend for jack, then run:

  **`pe.audio.sys/start.py all`**

The provided tool `bin/peaudiosys_view_brutefir.py` will help you on mapping outputs, delays, coeefs, filters running, polarity and gains.

When things seems to be ok, you can try to use the actual alsa sound card, but **still keep your AMP switched off**:

- Set the ALSA backend at `config.yml`

- **`pe.audio.sys/start.py stop`**

- **`pe.audio.sys/start.py all`**


