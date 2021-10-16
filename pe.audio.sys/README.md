# Credits

This is based on the former **FIRtro** and the current **pre.di.c** projects, as PC based digital preamplifier and crossover projects, designed by the pioneer **@rripio** and later alongside others contributors.


**https://github.com/rripio/pre.di.c**

**https://github.com/AudioHumLab/FIRtro/wiki**

The main software on which this project is based is **BRUTEFIR** a very versatile convolution engine with a real-time equalizer module.

**https://torger.se/anders/brutefir.html**


Wiring audio streams and sound card interfacing are based on **JACK https://jackaudio.org**

Most of the system is written in Python3, and config files are YAML kind of, thanks **@rripio**.

The control of the system is based on a tcp server architecture, thanks **@amr**.


# Features

The originary main features on FIRtro were:

- Digital crossover filtering and loudspeaker alignment, digital room correction, calibrated level control (based on the Brutefir convolution stages)

- Digital preamp facilities: bass, treble, equal loudness compensation curves, in-room target eq curves (based on the Brutefir runtime EQ module), as well a source selector based on the Jack audio server.

- Client/server arch controled by a web page
 
Additional features on **pe.audio.sys** are extended to involve:

- Music players management.
- Auxiliary system functions management (amplifier switching, ...).
- New control web page layout.

# Documentation

Please refer to the **`doc/`** folder
