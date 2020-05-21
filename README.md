# Credits

This is based on the former **FIRtro** and the current **pre.di.c** projects, as PC based digital preamplifier and crossover projects, designed by the pioneer **@rripio** and later alongside others contributors.


**https://github.com/rripio/pre.di.c**

**https://github.com/AudioHumLab/FIRtro/wiki**

The main software on which this project is based is **Brutefir** and its real-time equalizer module.

**https://torger.se/anders/brutefir.html**


# pe.audio.sys

A PC based personal audio system: preamp, digital crossover and media players management.

Some *end user* and *user friendly* features has been added here.

<a href="url"><img src="https://github.com/Rsantct/pre.di.c/blob/master/pre.di.c/clients/www/images/control%20web%20v2.0b.png" align="center" width="340" ></a>

## Highlights

- pe.audio.sys is hosted in a subfolder under your home folder, so it is independent of the user and you can have your stuff along with it.

- Install scripts to update your machine from github

- A lightweitght single page control web:

    - With metadata information and players control
    
    - Spotify Desktop or Spotify Connect embeded client integration.

    - A stream url can be entered into the web control page to start playing it.
    
    - EBU R128 Integrated Loudness Units (LU-I) visualizer to help desired SPL and loudness EQ-curves compensation level.

- A mouse can be used to control volume and mute easily.

- A LCD (usb4all) shows current settings and metadata

- IR daemon to use a remote


## Loudspeaker EQ and XOVER filtering

The preferred software for you to design your own FIRs (loudspeaker EQ and XOVER) is DSD:

**https://github.com/rripio/DSD**


## Room correction EQ (DRC)

Regarding room correction EQ, you can use both IIR (parametric correction) or FIR (impulse correction).

FIR DRC is supported under a reserver convolver stage on Brutefir.

IIR DRC can be used through by the provided Ecasound add-on script, then bypassing the convolver stage above.

The most popular software for room Eq is REW https://www.roomeqwizard.com

As experimental FIR DRC correction software you could also consider:

**https://github.com/rripio/DSC**

**https://github.com/Rsantct/DRC**

