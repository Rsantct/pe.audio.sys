# Integration with the PipeWire desktop sound server

Modern desktops uses PipeWire, for example Ubuntu 24.04 LTS.

Pipewire does EMULATE a PulseAudio like API, in order to players Apps like Spotify to reach the PW desktop sound server.

PW runs as a user session service.

PW integrates a Jack EMULATION, BUT we will NOT use that feature. We want **pe.audio.sys** to be compatible with headless systems without PW, through by our own native JACK sound server.

We will configure PipeWire in order to auto magically emerge a couple of jack ports named `PipeWire`, here we will have all the desktop audio streams, like Spotify.

## Pipewire configuration

Install the JACK sink: **`sudo apt install pipewire-jack`**

Prepare the following user session PipeWire setting files. You'll find a copy of these files under `.install/` directory in this repository.


        ~/.config/pipewire/
        │


        │
        ├── pipewire.conf.d
        │   │
                1. Prepares the PipeWire <--> JACK bridge
        │   ├── 10-paudio-jack.conf
        │   │

                2. Sets the default sink, for BOTH, PipeWire native clients
                   and Pulseaudio clients
            │
            └── 50-paudio-default-sink.conf

        │
        ├── client.conf.d

                2. Resampling settings for PipeWire native clients

        │   └── paudio-client.conf

                2. Resampling settings for PulseAudio clients

        │
        └── pipewire-pulse.conf.d
            └── paudio-pipewire-pulse.conf





You can fine tune the resample quality inside 
