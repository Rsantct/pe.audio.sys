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
