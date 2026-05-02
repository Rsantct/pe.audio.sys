## Network sources: JackTrip

https://www.jacktrip.com

You can send audio from another PC on the same LAN.

### local pe.audio.sys

Example:

pe.audio.sys/config/config.yml

    sources:

        MacBook Pro:
            jack_pname:      MacBook Pro
            jacktrip:        true            # This triggers the launch of the jacktrip server


### Remote Mac as remote source

You need to install:

- JackTrip (go to the offcial site to download the macOS installer)
- [BlackHole](https://github.com/ExistentialAudio/BlackHole) to route your audio. Please do not use the Homebrew installation method currently does not work, install it by downloading the [official package](https://existential.audio/blackhole).
