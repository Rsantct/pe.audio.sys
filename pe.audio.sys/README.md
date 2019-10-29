# Overview

The system is intended as a personal audio system based on a PC.

It is based on the former **FIRtro** and the current **pre.di.c** projects, from the pioneer **@rripio** and others contributors.

**https://github.com/AudioHumLab/FIRtro/wiki**

**https://github.com/rripio/pre.di.c**

Its main features are:

- Digital crossover for sophysticated loudspeakers management
- Preamplifier with loudness compensated and calibrated volume control.
- Web page for system control (FIRtro)

 Additional features on **pe.audio.sys** are extended to involve:

- Music players management.
- Auxiliary system functions management (amplifier switching, ...).
- New control web page behavoir.

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

The control of the system works through by **a TCP listening socket** that accepts **a set of commands**. Some commands have aliases to keep backwards compatibility from FIRtro or pre.di.c controllers.


### Getting info:

    state | status | get_state returns the whole system status parameters (.state.yml)
    get_eq                     returns the current Brutefir EQ stage (mag & pha)
    get_target_sets            list of target curves sets found under the loudspeaker folder
    get_drc_sets               list of drc sets
    get_xo_sets                list of xover sets

### Selector stage:

    input | source  <name>
    solo            off | l | r
    mono            off | on               ( aka mid )
    midside         off | mid | side
    mute            off | on

### Gain and Eq stage:

    level           xx [add]               xx in dB, use add for a relative adjustment
    balance         xx [add]
    treble          xx [add]
    bass            xx [add]
    loudness_ref    xx [add]
    loudness | loudness_track   on | off   loudness compensation
    set_target      <name>                 selects a target curve

### Convolver stages:

    set_drc | drc   <name>                 selects a DRC FIR set
    set_xo  | xo    <name>                 selects a XOVER FIR set


# Configuration

All system features are configured under **`config.yml`**. We provide a self commented **`config.yml.example`** file.

Few user scripts or shared modules can have an its own `xxx.yml` file of the same base name for configuration if necessary.


# Filesystem tree

All files are hosted under **`$HOME/pe.audio.sys`**, so that you can run `pe.audio.sys` under any user name.

That way you can keep any `~/bin` an other files and directories under your home directory.

1st level contains firsthand files (system  configuration and the system start script) and firsthand folders (loudspeakers, user macros).

Deeper `share/` levels contains runtime files you don't usually need to access to.

    $HOME/bin/              Some tools will be added to your ~/bin

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
    |-- pasysctrl           Command line tool to control the system
    |
    |-- start.py            This starts up or shutdown the whole system
    |
    |-- macros/             End user general purpose macro scripts (can have web interface buttons)
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

Loudspeaker config files kind of are leaved, only **`brutefir_config`** has to be adjusted to set the proper coeff levels and xover scheme, as well as system card wiring and delays on each port.

So *keep only useful files* under your loudspeaker folder, and *name them meaningfully*.

For control purposes, XO and DRC pcms will be scanned from the list of files found under the loudspeker folder. Please name files as follows:


DRC pcm files must be named:

    drc.<X>.DRCSETNAME.pcm   where X must be L | R


XO pcm files must be named:

    xo.<XX>.XOSETNAME.pcm    where XX must be fr | lo | mi | hi | sw

(fr: full range; lo,mi,hi: low,mid,high; sw: subwoofer)

# The config.yml file

This file allows to configure the whole system. We provide a **`config.yml.example`** with clarifying comments.

Some points:

- The list of service addressing here will trigger each service to be launched. The **`pasysctlr`** service is mandatory.
- The preamp loop ports will be automagically spawn under jack when source `capture_ports` below are named `xxx_loop`, so your player scripts have not to be aware of create loops, just configure the players to point to these preamp loops accordingly.

Here you are an uncommented example for `config.yml`:

    services_addressing:

        pasysctrl_address:      0.0.0.0
        pasysctrl_port:         9989

        aux_address:            localhost
        aux_port:               9988

        players_address:        localhost
        players_port:           9987

    system_card: hw:UDJ6

    external_cards:

    jack_options:           -R -d alsa
    jack_backend_options:   -d system_card -r 48000 -P -o 6

    loudspeaker: SeasFlat

    ref_level_gain: 0

    target_mag: target_mag_+3.0-1.0.dat
    target_pha: target_pha_+3.0-1.0.dat


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
    init_xo:                mp
    init_drc:               drc1
    init_input:             none

    gain_max: 6

    loudness_flat_curve_index: 7


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

    source_monitors:

    scripts:
        - sound_cards_prepare.py
        - mpd.py
        - istreams.py
        - pulseaudio-jack-sink.py
        - librespot.py

    aux:
        amp_on_cmdline:  /home/peaudiosys/bin/ampli.sh on
        amp_off_cmdline: /home/peaudiosys/bin/ampli.sh off



# The share/eq folder

This folder contains the set of curves that will be used to apply "soft" EQ to the system, i.e.: tone, loudness compensation and psychoacoustic room dimension equalization (aka 'target').

The curves will be rendered under the EQ stage on Brutefir.

Similar to the loudspeaker folder, some rules here must be observed when naming files:

- Frequencies: `xxxxxxfreq.dat`
- Tone: `xxxxxxbass_mag.dat xxxxxxbass_pha.dat xxxxxxtreble_mag.dat xxxxxxtreble_pha.dat` 
- Loudness: `xxxxxxloudness_mag.dat xxxxxxloudness_pha.dat`
- Target: `yyyyyytarget_mag.dat yyyyyytarget_pha.dat` ... ...

On freq, tone and loudness files the xxxxxx part is optional.

On target files yyyyyyy is also optional but neccessary if more than one target set is desired.

You can issue the commands **`get_target_sets`** and **`set_target yyyyyytarget`** to manage the target eq.


