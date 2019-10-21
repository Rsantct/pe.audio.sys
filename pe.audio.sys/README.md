# Overview

The system is intended as a personal audio system based on a PC. It is based on the former **FIRtro** and the current **pre.di.c** projects, from the pioneer @rripio and others contributors.

https://github.com/AudioHumLab/FIRtro/wiki

https://github.com/rripio/pre.di.c

Its main features are:

- Digital crossover for sophysticated loudspeakers management
- Preamplifier with loudness compensated and calibrated volume control.
- Web page for system control (only on FIRtro)

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


# Configuration

All system features are configured under `config.yml`. This file is self commented.

Few user scripts or shared modules can have an YAML of the same name for configuration if necessary.


# Filesystem tree

1st level contains 1st hand files (system  configuration and the system start script) and folders (loudspeakers, user macros).

Deeper `share/` levels contains runtime files you don't usually need to access to.

    pe.audio.sys/
    |
    |-- README.md           this file
    |
    |-- config.yml          the main configuration file
    |
    |-- xxxx.yml            other configuration files
    |
    |-- .asound.XXX         ALSA sound cards restore settings, see sound_cards_prepare.py under scripts/
    |
    |-- pasysctrl           command line tool to control the system
    |
    |-- start.py            this starts up or shutdown the whole system
    |
    |-- macros              end user general purpose macro scripts (can have web interface buttons)
    |
    |-- share/              system modules (the core and the tcp server)
    |   |
    |   |-- eq/             tone, loudness and target curves .dat files
    |   |
    |   |-- services/       services provided under the server (system control and others)
    |   |
    |   |-- scripts/        additional scripts that can be launched at start up
    |   |
    |   \-- www/            a web interface to control the system
    |
    \-- loudspeakers/       
        |
        |-- lspk1/          loudspeaker files: brutefir_config, xo & drc pcm FIRs
        |-- lspk2/
        |-- ...
     


# The loudspeaker

Loudspeaker config files kind of are leaved, only **`brutefir_config`** has to be adjusted to set the proper coeff levels and xover scheme, as well as system card wiring and delays on each port.

For control purposes, XO and DRC pcms will be scanned from the list of files found under the loudspeker folder,
when named as follows:


DRC pcm files must be named:

    drc.<X>.DRCSETNAME.pcm   where X must be L | R


XO pcm files must be named:

    xo.<XX>.XOSETNAME.pcm    where XX must be fr | lo | mi | hi | sw
