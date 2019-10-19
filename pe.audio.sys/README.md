# Overview

The system is intended as a personal audio system based on a PC. It is based on the former **FIRtro** and the current **pre.di.c** projects. Its main features:

- Digital crossover for sophysticated loudspeakers management
- Preamplifier with loudness compensated and calibrated volume control.
- Web page for system control (only on FIRtro)

 Additional features on **pe.audio.sys**:

- Music players management.
- Auxiliary system functions management.
- New control web page behavoir.

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
    |-- loudspeakers/       
    |   |
    |   |-- lspk1           loudspeaker files: brutefir_config, xo & drc pcm FIRs
    |   |-- ...
    |
    |-- scripts/            additional scripts to launch at start up
    |
    \-- www/                the control web page


# The loudspeaker

XO and DRC pcms will be scanned from the list of files found under the loudspeker folder,
when named as follows:


DRC pcm files must be named:

    drc.<X>.DRCSETNAME.pcm   where X must be L | R




XO pcm files must be named:

    xo.<XX>.XOSETNAME.pcm    where XX must be fr | lo | mi | hi | sw
