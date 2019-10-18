# pe.audio.sys

A PC based personal audio system: preamp, digital crossover and media players management.

This is based on **FIRtro** https://github.com/AudioHumLab/FIRtro/wiki and  **pre.di.c**  https://github.com/rripio/pre.di.c, a PC based digital preamplifier and crossover projects.

Some *end user* and *user friendly* features has been added here.

<a href="url"><img src="https://github.com/Rsantct/pre.di.c/blob/master/pre.di.c/clients/www/images/control%20web%20v2.0b.png" align="center" width="340" ></a>

## Highlights

- Install scripts to update your machine from github

- A lightweitght single page control web:

    - With metadata information and players control
    
    - Spotify Desktop or Spotify Connect embeded client integration.

    - A stream url can be entered into the web control page to start playing it.
    
    - Integrated Loudness program visualizer for loudness tracking

- A mouse can be used to control volume and mute easily.

- A LCD (usb4all) shows current settings and metadata


## room correction EQ

Regarding your room correction EQ, you can use both IIR (parametric correction) or FIR (impulse correction). I prefer the last one, and I propose multipoint based correction, for example you can try my [multipoint DRC](https://github.com/Rsantct/DRC).

This is an audio system based on the former FIRtro and the current pre.di.c projects.

# Overview

The system is intended as a personal audio system based on a PC. The features:

    - Digital crossover for sophysticated loudspeakers management
    - Preamplifier with loudness compensated and calibrated volume control.
    - Music players management.
    - Auxiliary system functions management.

Most of the system is written in Python3, and config files are YAML kind of.

The control of the system is based on a tcp server architecture.

The core is mainly based on:

    - JACK: a sound server (wiring audio streams and sound card interfacing)

    - BRUTEFIR, a convolution engine that supports:

        - XOVER FIR filtering (multiway active loudspeaker crossover filtering)
        - DRC FIR filtering (digital room correction)
        - EQ: bass, treble, dynamic loudness curves, in-room target eq curves.
        - LEVEL control


# Configuration

All system features are configured under `config.yml`. This file is self commented.

User scripts or shared modules can have an YAML of the same name for configuration if necessary.


# Filesystem tree


    pe.audio.sys/
    |
    |-- README.md           this file
    |
    |-- config.yml          the main configuration file
    |
    |-- pasysctrl           command line to control the system
    |
    |-- start.py            this starts up the whole system
    |
    |-- core/               the core modules
    |
    |-- share/              general purpose modules and files
    |
    |-- eq/                 tone, loudness and target curves .dat files
    |
    |-- loudspeakers/       loudspeaker files: brutefir_config, xo & drc FIRs
    |   |
    |   |-- lspk1                                          
    |   |-- ...
    |
    |-- scripts/            additional scripts to launch at start up
    |
    \-- www/                the control web page


# The loudspeaker

XO and DRC pcms will be scanned from the list of files found under the loudspeker folder,
when named as follows:


- DRC pcm files must be named:

    drc.X.DRCSETNAME.pcm   where X must be L | R

    0123456.........-4    



- XO pcm files must be named:

    xo.XY.XOSETNAME.pcm   where XY must be fr | lo | mi | hi | sw

    0123456........-4    

 
