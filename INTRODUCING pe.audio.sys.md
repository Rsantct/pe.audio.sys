
# Introducing pe.audio.sys


**pe.audio.sys** is a versatile and **fully customizable** PC based audio system.

Its main feature is the management, filtering and EQ of a **multiway active
loudspeaker system**. A regular passive loudspeakers can be used as well.

Full hi-fi preamplifier features are available.

In addition, you can control unlimited audio sources:

- External audio sources:

    - DVB-T radio (USB dongle)
    - Apple TV box, cable TV
    - TV
    - Analog sources (FM, vinyl, ...)
    - etc ...

- Internal audio sources:

    - CD drive
    - Internet radio
    - Spotify
    - Hard Disk mp3/flac/aiff/wav files
    - Desktop apps (i.e: Youtube, etc )


## EQ capabilities:

- Loudspeaker anechoic correction
- Digital Room Correction
- Multiway crossover
- Advanced FIR filtering or traditional IIR filtering
- Target EQ curves for subjective in room responses


## System control

Simple control from your smartphone or tablet.

The whole system is **controlled by a lightweight single web page**:

<a href="url"><img src="https://github.com/Rsantct/pre.di.c/blob/master/pre.di.c/clients/www/images/control%20web%20v2.0b.png" align="center" width="340" ></a>

Main control web features are:

- **Calibrated volume listening** supported by an EBU R128 Loudness monitor.

- Calibrated **equal loudness compensation curves** (ISO 226:2003 standard) for low SPL listening without loosing low and high bands perception

- Hi-Fi preamp controls (volume, tone, balance, stereo/mono, mute, loudness, source selector, amplifier on/off)

- User defined presets for EQ modes and xover FIR filtering

- User defined macro buttons for easy listening to file playlist or Spotify playlists, preferred radio stations, etc...

- Displays metadata, bitrate and time of playback sources.

- Playback control (pause, next, prev, etc) for integrated players (Spotify desktop, MPD daemon, CD).


As an option, the system can be controlled by a **remote IR**, as well a standard 4 lines **LCD display** for basic information and playback metadata visualization.

A mouse attached to a pe.audio.sys 'black box' can be used as a easy-access volume/mute control.


## System maintenace

An simple script will update the whole system from GitHub, without user intervention. 


## System usage and configuration

See **`doc/`** folder and `90_FAQ.md`


# Some use cases


## 'Black box' or 'Desktop' configuration

pe.audio.sys is designed to be a **'black box'** headless system, no monitor keyboard or mouse are needed at all. If needed, you can stream audio wirelessly from your smartphone or tablet to the 'black box'.

In addition, the system can be easily integrated in a **Linux Desktop with monitor, keyboard and mouse**, no special configurations are needed. This way you can listen to your favourite desktop applications as Spotify, Youtube, watching movies, etc...

My preferred system configuration is a **'headless Desktop'**, because this way you can have Spotify Desktop to provide full metadata info to be displayed under the control web page or the optional LCD display, without needing an attached monitor. Anyway you can use your TV-hdmi as monitor when playing desktop movies.


## Hard Disk music files library

MPD (Music Player Daemon) is integrated as the player for your audio files.

You can control your playback in several ways:

- Web page user defined buttons (max 100) for launching favourites playlist to be played
- Web playback control buttons: next, previous, pause, ...
- A samartphone/tablet MPD app for a total control of the music library
- A desktop MPD application (desktop mouse and keyboard)


## CD discs

You can play CD directly on your CD drive unit, or by an external CD player.

When you use the internal one drive, the CD metadata (artist, album, title) will
be displayed on the control web page or on the optional LCD display.


## Spotify (premium)

You can use your smartphone or tablet Spotify App to control the integrated Spotify player.

So the Spotify App simply controls the _Spotify connect_ client inside pe.audio.sys, but the audio stream comes directly from the
internet to your system loudspeakers.

In a desktop system, you can also use a Linux desktop Spotify application.


## Radio stations

In current days, the best audio quality radio is available from the TV terrestial broadcast network (DVB-T). You will need a DVB-T USB dongle, see details under the `/doc/90_FAQ.md` and `share/scripts/DVB-T.py`.

In addition, you can listen to Internet Radio stations or audio streams without any extra hardware, see `share/scripts/istreams.py`.

Also, a classical FM tuner can be attached via analog sound card inputs.


## Amplifier power on/off

A script is provided for you to switch a relay USB controlled socket strip.


## Multiroom audio

You can easily configure two networked pe.audio.sys loudspeaker systems to listen from each
other. 

If desired, the volume level on both can be linked.


## Switch over from my iPhone

When arriving home while listening to your favourite podcast through by your iPhone phones, you can easily
switch to listen through by your pe.audio.sys loudspeakers:

- Power on pe.audio.sys, then select source: Airplay (integrated) or Apple TV (optional external)

- On your iPhone select Airplay 'pe.audio.sys' (or 'Apple TV').


