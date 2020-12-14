# Credits

This is based on the former **FIRtro** and the current **pre.di.c** projects, as PC based digital preamplifier and crossover projects, designed by the pioneer **@rripio** and later alongside others contributors.


**https://github.com/rripio/pre.di.c**

**https://github.com/AudioHumLab/FIRtro/wiki**


The main software on which this project is based is **Brutefir** and its real-time equalizer module.

**https://torger.se/anders/brutefir.html**


# Overview

The system is intended as a personal audio system based on a PC.

The originary main features are:

- **Digital crossover** for sophysticated loudspeakers management
- Preamplifier with **calibrated volume control and equal loudness compensation eq**.
- **Web page for system control** (FIRtro)

 Additional features on **pe.audio.sys** are extended to involve:

- Music players management.
- Auxiliary system functions management (amplifier switching, ...).
- New control web page layout.

Most of the system is written in Python3, and config files are YAML kind of, thanks **@rripio**.

The control of the system is based on a tcp server architecture, thanks **@amr**.

The system core is mainly based on:

- JACK: the sound server (wiring audio streams and sound card interfacing)

- BRUTEFIR, a convolution engine that supports:

    - XOVER FIR filtering (multiway active loudspeaker crossover filtering)
    - DRC FIR filtering (digital room correction)
    - EQ: bass, treble, dynamic loudness compensation curves, in-room target eq curves.
    - LEVEL control.

# Controling the system

- A web page front end is provided so you can easily control the system as well your integrated music players.

- An IR interface is provided to control through by an infrared remote.

Anyway the control of the system works through by **a TCP listening socket** that accepts **a set of commands**.

Some commands have aliases to keep backwards compatibility from FIRtro or pre.di.c controllers.

## Preamp control

All commands prefixed with `preamp`. This prexix can be omited.

### Geeting help
 
    help                        This help

### Getting info:

    state | status | get_state  Returns the whole system status parameters,
                                as per stored in .state.yml
    get_inputs                  List of available inputs
    get_eq                      Returns the current Brutefir EQ stage (freq, mag ,pha)
    get_target_sets             List of target curves sets available under the eq folder
    get_drc_sets                List of drc sets available under the loudspeaker folder
    get_xo_sets                 List of xover sets available under the loudspeaker folder

### Selector stage:

    input | source  <name>
    solo            off |  l  | r
    mono            off | on  | toggle      ( aka midside => mid )
    midside         off | mid | side
    polarity        ++  | +-  | -+  | --    LR polarity
    mute            off | on  | toggle

### Gain and Eq stage:

    level           xx [add]               'xx' in dB, use 'add' for a relative adjustment
    balance         xx [add]
    treble          xx [add]
    bass            xx [add]
    lu_offset       xx [add]
    loudness        on | off | toggle       Equal loudness contour correction
    set_target       <name>                 Selects a target curve

### Convolver stages:

    set_drc | drc    <name>                 Selects a DRC FIR set
    set_xo  | xo     <name>                 Selects a XOVER FIR set

### Energy saving:

    powersave        on | off               Enables auto switching off the convolver when the
                                            preamp signal drops below a noise floor for a while


## Music players control

All commands prefixed with `player`:

    state                                   Gets the playback state: play, pause or stop.

    stop | pause | play | play_track_NN
    next | previous | rew | ff              Controls the playback
    
    eject                                   Ejects the CD tray
    
    http://url                              Plays the internet audio stream from a given url
    
    load_playlist  <plist_name>             Tells the current player to load a playlist

    get_playlists                           Gets the available playlist from the current player
    
    get_meta                                Gets metadata info from current player if available 
    

## Miscel controls

All commands prefixed with `aux`:

    amp_switch   on | off                   Switch an amplifier
    
    LU_monitor_reset                        Force to reset the LU-I measure

    get_LU_monitor                          Gets the monitored LU-I value and scope
    
    set_LU_monitor_scope  album | track     Choose the LU-I metering scope

    restart                                 Restarts pe.audio.sys
    
    add_delay   xx                          Delays xx ms the sound card outputs, e.g for multiroom listening


## Monitoring the system

The provided web page will show the system status as well music player's information.

An LCD service is provided to plug a LCD display to show the system status as well metadata from players.

You can also use the above getting info commands, through by a TCP connection.

## Monitorig the EBU R128 LU-I Integrated Loudness of the audio signal

Most music rock and pop kind of records from 80's onwards have been mastered under the 'loudness war' age.

To deal with this, you can load an optional script `loudness_monitor.py` under your `config.yml` preferences.

This script will automatically measure the EBU R128 LU-I Integrated Loudness of the current preamp source.

The monitored value will be available in several flavours:

- A graphic bar 'LU monitor' is displayed inside the control web page.
- The LCD will also display the 'LUmon' value.
- By a special command: `aux get_LU_monitor`.

A **reset** function is also provided for the monitored LU value, by a web button or by command line.

An auto reset will occur when **changing the preamp input**. In addition, the LU value could be reset also when **the played album or title (track) changes** (option inside `config.yml`).

To compensate for high LU-Integrated values on your listening audio program, we provide some options:

- The control web offers a 'LU offset' slider for you to compensate the displayed LU monitor value: simply adjust the slider as per the displayed bar span. For convenience, the adjusted value steps in 3 dB from 0 to 12 dB.
- You can preset an estimated 'lu_offset' value under your favourite sources inside `config.yml`
- You can prepare your own macros (linked to control web buttons). For instance you can set 0 dB for classical radio stations, or say about 9 dB for pop & rock radio stations.


This way, the loudness compensation feature of the calibrated volume control of pe.audio.sys will apply the appropriate contour curve when you listen below your reference SPL (level = 0 dBSPL).
 
It is planned to provide a servo feature for tracking the monitored LU then auto adjust the LU offset compensation.

<a href="url"><img src="https://github.com/AudioHumLab/pe.audio.sys/raw/master/pe.audio.sys/doc/images/LU_monitor.png" align="center" width="400" ></a>

## Tools

Some nice tools are provided under your `~/bin` folder, below a brief description.

    $HOME/bin/
          |
     ____/
    /
    |-- peaudiosys_control                  A command line tool to issue commands to the system
    |
    |-- peaudiosys_server_restart.sh        Restart or stop the server (use --help for usage howto)
    |
    |-- peaudiosys_view_brutefir.py         Shows the running Brutefir configuration:
    |                                       mapping to sound card ports, coeffs and filters running
    |
    |-- peaudiosys_plot_brutefir_eq.py      Plot the runtime EQ module in Brutefir
    |
    |-- peaudiosys_plot_eq_curves.py        A tool to plot the curves under the share/eq folder


Advanced tools to prepare preamp eq stuff can be found in `http://AudioHumLab/audiotools/brutefir_eq`.


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
    |-- pasysctrl.hlp       Help on system control commands
    |
    |-- .state.yml          The file that keeps the run-time system state
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
    |-- doc/                Support documents
    |
    |-- loudspeakers/       
    |   |
    |   |-- lspk1/          Loudspeaker files: brutefir_config, xo & drc pcm FIRs
    |   |-- lspk2/
    |   |-- ...
    |
    \-- share/              System folders
        |
        |-- audiotools/     Auxiliary programs from the AudioHumLab/audiotools repository
        |
        |-- eq/             Shared tone, loudness and target curves .dat files
        |
        |-- services/       Services to manage the whole system
        |
        |-- scripts/        Additional scripts to launch at start up when issued at config.yml,
        |                   advanced users can write their own here.
        |
        \-- www/            A web interface to control the system



# Configuration: the `config.yml` file

All system features are configured under **`config.yml`**.

We provide a **`config.yml.sample`** with clarifying comments, please take a look on it because you'll find there some useful info.

Few user scripts or shared modules can have its own `xxx.yml` file of the same base name for configuration if necessary.

This file allows to configure the whole system.

Some points:

- The necessary preamp **loop ports** will be auto spawn under JACK when source `capture_ports` are named `xxx_loop` under the `sources:` section, so your player scripts have not to be aware of create loops, just configure the players to point to these preamp loops accordingly.

- You can force some audio **settings at start up**, see `init_xxxxx` options.

- You can force some audio **settings when change the input source**, see `on_change_input:` section.


Here you are an uncommented bare example of `config.yml`:


    system_card: hw:UDJ6

    external_cards:

    jack_options:           -R -d alsa
    jack_backend_options:   -d $autoCard -r $autoFS -P -o 6


    balance_max:       6.0
    gain_max:          0.0
    eq_loud_ceil:      false
    bfeq_linear_phase: false

    loudspeaker:    SeasFlat
    refSPL:         83
    ref_level_gain: -10.0

    on_init:
        xo:                 mp
        drc:                mp_multipV1
        target:             +4.0-2.0_target
        level:              
        max_level:          -20
        muted:              false
        bass:               0
        treble:             0
        balance:            0
        equal_loudness:     true
        lu_offset:          6.0     # most records suffers loudness war mastering
        midside:            'off'
        solo:               'off'
        input:              'mpd'

    run_macro: '7_mpd_play_mylist'

    on_change_input:
        bass:               0.0
        treble:             0.0
        equal_loudness:     True
        lu_offset:          6.0     # most records suffers loudness war mastering
        midside:           'off'
        solo:              'off'

    sources:
    
        spotify:
            capture_port:   alsa_loop
            gain:           0.0
            xo:             lp
        mpd:
            capture_port:   mpd
            gain:           0.0
            xo:             lp
        istreams:
            capture_port:   mplayer_istreams
            gain:           0.0
            xo:             lp
        tv:
            capture_port:   system
            gain:           +6.0                # low level source
            xo:             mp                  # low latency filtering
            target:         +0.0-0.0_target     # preferred for movie dialogue
        remote:
            capture_port:   zita-n2j
            gain:           0.0
            xo:             lp
            address:        192.168.1.234

    source_monitors:

    scripts:
        - sound_cards_prepare.py
        - mpd.py
        - istreams.py
        - pulseaudio-jack-sink.py
        - librespot.py
        - zita-n2j_mcast.py

    peaudiosys_address:     localhost
    peaudiosys_port:        9990

    amp_manager:            /home/predic/bin/ampli.sh
    amp_off_stops_player:   true

    restart_cmd: peaudiosys_restart.sh

    web_config:
        hide_LU: false
        show_graphs: true
        main_selector: 'inputs'
        

    LU_reset_scope: album

    cdrom_device:  /dev/cdrom

    powersave:              true
    powersave_noise_floor:  -70
    powersave_max_wait:     180  # Time in seconds before shutting down Brutefir

    spotify_playlists_file: spotify_plists.yml

# The share/eq folder

This folder contains the set of curves that will be used to apply "soft" EQ to the system, i.e.: tone, loudness compensation and psychoacoustic room dimension equalization (aka 'target').

(i) The curves will be rendered under the EQ stage on Brutefir, so your `brutefir_config` file must have an `"eq"` section properly configured with the same frequency bands as the contained into your `freq.dat` file. More info: https://torger.se/anders/brutefir.html#bflogic_eq

Similar to the loudspeaker folder, some rules here must be observed when naming files:

- Frequencies: `freq.dat`
- Tone:        `bass_mag.dat bass_pha.dat treble_mag.dat treble_pha.dat` 
- Loudness:    `ref_XX_loudness_mag.dat ref_XX_loudness_pha.dat` (as many as reference SPL you want to manage)
- Target:      `+X.X-Y.Y_target_mag.dat +X.X-Y.Y_target_pha.dat` ... ...

On target files '+X.X-Y.Y_' is also optional but neccessary if more than one target set is desired to be available to be switched.

You can issue the commands **`get_target_sets`** and **`set_target +X.X-Y.Y_target`** to manage the target eq.

A sets of tone, loudness and target curves are provided on this distro:

- `share/eq.sample.R20_audiotools/` from the `audiotools` project. Loudness contour curves here span from 0 to 90 phon. Tone curves and room gain house curve have a 1st order slope.

- `share/eq.sample.R20_ext/` from the `FIRtro` and `pre.di.c` projects by the pioneer @rripio. Loudness contour curves here span from 70 to 90 phon. Tone curves and room gain house curve have a 2nd order slope.

You can make your own EQ curves by running the tools provided here:

https://github.com/AudioHumLab/audiotools/tree/master/brutefir_eq

You can easily visualize the system available curves under `share/eq` by using the command line tool `peaudiosys_plot_eq_curves.py`

### Optional share/eq files

If you want to use another sound processors, you can hold here some more files.

For instance, you can use Ecasound to add a parametric EQ processor before Brutefir, for more info see the section `scripts:` under the provided `config.yml.sample` file.

# The audio routing

Here you are a typical JACK wiring screenshot.

The selected source is an MPD player wich is configured to point to the mpd_loop ports.

The preamp has a unique entrance point: the pre_in_loop. This loops feeds the main audio processor, i.e Brutefir.

You can add another audio processor, e.g. an Ecasound parametric EQ plugin. We provide hera a script that INSERTS it after the pre_in_loop and before the Brutefir input.

You are free to insert any other sound processor, Jack is your friend. To automate it on start up, you can prepare an appropriate script.

Brutefir is the last element and the only one that interfaces with the sound card Jack ports. The loudspeakers are a two way set, connected at the last sound card ports. 

![jack_wiring](https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/doc/images/jack_routing_sample.png)


# The loudspeaker

Loudspeaker config files kind of are leaved, only **`brutefir_config`** has to be adjusted to set the proper coeff levels and xover scheme, as well as the system card wiring and the delays on each port.

( for more info on `brutefir_config` please see `doc/Configuration.md` )

So *keep only useful files* under your loudspeaker folder, and *name them meaningfully*.

For control purposes, XO and DRC pcms will be scanned from the list of files found under the loudspeker folder.

Please name files as follows:


DRC pcm files must be named:

    drc.X.DRCSETNAME.pcm      where X must be L | R

XO pcm files must be named:

    xo.XX[.C].XOSETNAME.pcm   where XX must be:  fr | lo | mi | hi | sw
                              and channel C is OPTIONAL, can be: L | R

    Using C allows to have DEDICATED DRIVER FIR FILTERING if desired.  

    (fr: full range; lo,mi,hi: low,mid,high; sw: subwoofer)

### Full range loudspeaker w/o correction 'xo' filter

If you want not to use any xo filter at all, you simply do:

- configure `brutefir_config` with coeff -1:

        filter "f.fr.L" {
            from_filters: "f.drc.L";
            to_outputs:   "fr.L"/0.0/+1;
            coeff:        -1;
        };

        filter "f.fr.R" {
            from_filters: "f.drc.R";
            to_outputs:   "fr.R"/0.0/+1;
            coeff:        -1;
        };

- Leave blank `xo:` inside `on_init` section from `config.yml` 

- Leave blank `xo_set:` inside `.state.yml`

- Omit any `xo....pcm` file inside your loudspeaker folder.





