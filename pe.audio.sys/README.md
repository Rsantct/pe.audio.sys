# Credits

This is based on the former **FIRtro** and the current **pre.di.c** projects, as PC based digital preamplifier and crossover projects, designed by the pioneer **@rripio** and later alongside others contributors.

### https://github.com/rripio/pre.di.c

### https://github.com/AudioHumLab/FIRtro/wiki


# Overview

The system is intended as a personal audio system based on a PC.

The originary main features were:

- Digital crossover for sophysticated loudspeakers management
- Preamplifier with loudness compensated and calibrated volume control.
- Web page for system control (FIRtro)

 Additional features on **pe.audio.sys** are extended to involve:

- Music players management.
- Auxiliary system functions management (amplifier switching, ...).
- New control web page layout.

Most of the system is written in Python3, and config files are YAML kind of, thanks **@rripio**.

The control of the system is based on a tcp server architecture.

The system core is mainly based on:

- JACK: the sound server (wiring audio streams and sound card interfacing)

- BRUTEFIR, a convolution engine that supports:

    - XOVER FIR filtering (multiway active loudspeaker crossover filtering)
    - DRC FIR filtering (digital room correction)
    - EQ: bass, treble, dynamic loudness curves, in-room target eq curves.
    - LEVEL control

# Controling the system

A web page front end is provided so you can easily control the system as well your integrated music players.

**@rripio** has also an IR interface than can be adapted to control through by an infrared remote.

Anyway the control of the system works through by **a TCP listening socket** that accepts **a set of commands**.

Some commands have aliases to keep backwards compatibility from FIRtro or pre.di.c controllers.


### Getting info:

    state | status | get_state  returns the whole system status parameters,
                                also stored in .state.yml
    get_eq                      returns the current Brutefir EQ stage (freq, mag ,pha)
    get_target_sets             list of target curves sets available under the eq folder
    get_drc_sets                list of drc sets available under the loudspeaker folder
    get_xo_sets                 list of xover sets available under the loudspeaker folder

### Selector stage:

    input | source  <name>
    solo            off |  l  | r
    mono            off | on  | toggle     ( aka midside => mid )
    midside         off | mid | side
    mute            off | on  | toggle

### Gain and Eq stage:

    level           xx [add]               'xx' in dB, use 'add' for a relative adjustment
    balance         xx [add]
    treble          xx [add]
    bass            xx [add]
    loudness_ref    xx [add]
    loudness | loudness_track     on | off | toggle   loudness compensation
    set_target       <name>                           selects a target curve

### Convolver stages:

    set_drc | drc    <name>                 selects a DRC FIR set
    set_xo  | xo     <name>                 selects a XOVER FIR set

## Monitoring the system

The provided web page will show the system status as well music player's information.

An LCD service is provided to plug a LCD display to show the system status as well metadata from players.

You can also use the above getting info commands, through by any TCP connection.

## Tools

Some nice tools are provided under your `~/bin` folder, below a brief description.

    $HOME/bin/
          |
     ____/
    /
    |-- peaudiosys_control                  A command line tool to issue commands to the system
    |
    |-- peaudiosys_service_restart.sh       Restart or stop a service (more info on config.yml)
    |
    |-- peaudiosys_view_brutefir.py         Shows the running Brutefir configuration:
    |                                       mapping to sound card ports, coeffs and filters running.
    |
    |-- peaudiosys_view_eq_curves.py        A tool to plot the curves under the share/eq folder
    |
    |-- peaudiosys_do_target.py             Make target curves



# Filesystem tree

All files are hosted under **`$HOME/pe.audio.sys`**, so that you can run `pe.audio.sys` under any user name.

That way you can keep any `~/bin` an other files and directories under your home directory.

1st level contains the firsthand files (system configuration and the system start script) and the firsthand folders (loudspeakers, user macros).

Deeper `share/` levels contains runtime files you don't usually need to access to.


    $HOME/pe.audio.sys/
          |
     ____/
    /
    |-- README.md           This file
    |
    |-- config.yml          The main configuration file
    |
    |-- xxxx.yml            Other configuration files
    |
    |-- .asound.XXX         ALSA sound cards restore settings, see scripts/sound_cards_prepare.py
    |
    |-- start.py            This starts up or shutdown the whole system
    |
    |-- macros/             End user general purpose macro scripts (e.g. web interface buttons)
    |
    |-- doc/                Help documents
    |
    |-- loudspeakers/       
    |   |
    |   |-- lspk1/          Loudspeaker files: brutefir_config, xo & drc pcm FIRs
    |   |-- lspk2/
    |   |-- ...
    |
    \-- share/              System modules (the core and the tcp server)
        |
        |-- eq/             Tone, loudness and target curves .dat files
        |
        |-- services/       Services provided through by the tcp server (system control and others)
        |
        |-- scripts/        Additional scripts that can be launched at start up
        |
        \-- www/            A web interface to control the system



# The loudspeaker

Loudspeaker config files kind of are leaved, only **`brutefir_config`** has to be adjusted to set the proper coeff levels and xover scheme, as well as the system card wiring and the delays on each port.

So *keep only useful files* under your loudspeaker folder, and *name them meaningfully*.

For control purposes, XO and DRC pcms will be scanned from the list of files found under the loudspeker folder.

Please name files as follows:


DRC pcm files must be named:

    drc.<X>.DRCSETNAME.pcm   where X must be:    L | R


XO pcm files must be named:

    xo.<XX>.XOSETNAME.pcm    where XX must be:  fr | lo | mi | hi | sw

(fr: full range; lo,mi,hi: low,mid,high; sw: subwoofer)



# Configuration: the `config.yml` file

All system features are configured under **`config.yml`**. We provide a **`config.yml.example`** with clarifying comments.

Few user scripts or shared modules can have its own `xxx.yml` file of the same base name for configuration if necessary.

This file allows to configure the whole system.

Some points:

- The **list of services** addressing here will trigger auto launching each service. The **`pasysctlr`** service is mandatory.

- The necessary preamp **loop ports** will be auto spawn under JACK when source `capture_ports` are named `xxx_loop` under the `sources:` section, so your player scripts have not to be aware of create loops, just configure the players to point to these preamp loops accordingly.

Here you are an uncommented bare example of `config.yml`:


    services_addressing:

        pasysctrl_address:      0.0.0.0
        pasysctrl_port:         9989

        aux_address:            localhost
        aux_port:               9988

        players_address:        0.0.0.0
        players_port:           9987

    system_card: hw:UDJ6

    external_cards:

    jack_options:           -R -d alsa
    jack_backend_options:   -d system_card -r 48000 -P -o 6


    balance_max:    6.0
    ref_level_gain: -10.0
    gain_max:       0.0


    loudspeaker: SeasFlat

    init_xo:                mp
    init_drc:               mp_multipV1
    init_target:            +3.0-1.0_target

    init_mute:              'off'
    init_level:             
    init_max_level:         -20
    init_bass:              0
    init_treble:            0
    init_balance:           0
    init_loudness_track:    'on'
    init_loudness_ref:      0
    init_midside:           'off'
    init_solo:              'off'
    init_input:             salon

    sources:
        spotify:
            capture_port:   alsa_loop
            gain:           0.0
            xo:             mp
        mpd:
            capture_port:   mpd_loop
            gain:           0.0
            xo:             mp
        istreams:
            capture_port:   istreams_loop
            gain:           0.0
            xo:             mp
        salon:
            capture_port:   zita-n2j
            gain:           0.0
            xo:             mp

    source_monitors:

    scripts:
        - sound_cards_prepare.py
        - mpd.py
        - istreams.py
        - pulseaudio-jack-sink.py
        - librespot.py
        - zita-n2j_mcast.py

    aux:
        amp_on_cmdline:  /home/peaudiosys/bin/ampli.sh on
        amp_off_cmdline: /home/peaudiosys/bin/ampli.sh off


# The share/eq folder

This folder contains the set of curves that will be used to apply "soft" EQ to the system, i.e.: tone, loudness compensation and psychoacoustic room dimension equalization (aka 'target').

(i) The curves will be rendered under the EQ stage on Brutefir, so your `brutefir_config` file must have an `"eq"` section properly configured with the same frequency bands as the contained into your xxxxxxxfreq.dat file. More info: https://www.ludd.ltu.se/~torger/brutefir.html#bflogic_eq

Similar to the loudspeaker folder, some rules here must be observed when naming files:

- Frequencies: `xxxxxxfreq.dat`
- Tone: `xxxxxxbass_mag.dat xxxxxxbass_pha.dat xxxxxxtreble_mag.dat xxxxxxtreble_pha.dat` 
- Loudness: `xxxxxxloudness_mag.dat xxxxxxloudness_pha.dat`
- Target: `yyyyyytarget_mag.dat yyyyyytarget_pha.dat` ... ...

On freq, tone and loudness files the xxxxxx part is optional.

On target files yyyyyyy is also optional but neccessary if more than one target set is desired.

You can issue the commands **`get_target_sets`** and **`set_target yyyyyytarget`** to manage the target eq.

The set of tone and loudness curves provided on this distro are the ones from the original **FIRtro** project from the pioneer **@rripio**

You can easily visualize these curves by using the command line tool `peaudiosys_view_eq_curves.py`


