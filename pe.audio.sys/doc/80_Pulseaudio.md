
## Install Pulseaudio

Pulseadio is the standard sound server on Linux desktops.

Anyway it is interesting for a headless system based in JACK, because some music sources works well through by Pulseaudio instead of Jack.

### Desktop system

A desktop machine already have Pulseaudio installed, you'll need just some modules:

    sudo apt install    pulseaudio-module-jack pulseaudio-module-bluetooth

### Headless system:

    sudo apt install    pulseaudio pulseaudio-utils pavucontrol \
                        pulseaudio-module-jack pulseaudio-module-bluetooth


### Pulseaudio services (systemd)

- Check systemd services (normally disabled after installation):

        systemctl        status pulseaudio      # system wide scope
        systemctl --user status pulseaudio      # user scope

- Enable Pulseadio for your user:

        systemctl --user enable pulseaudio
        systemctl --user start pulseaudio


- Disable the system wide service if necessary

        systemctl  stop    pulseaudio
        systemctl  disable pulseaudio

### Pulseaudio configuration `/etc/pulse/daemon.conf`

Check the available resample methods:

        $ pulseaudio --dump-resample-methods

Configure in `/etc/pulse/daemon.conf`:

        resample-method = soxr-vhq
        avoid-resampling = no
        realtime-scheduling = yes


### pe.audio.sys

- **pe.audio.sys** will automatically ask Pulseaudio to release the sound card to run Jack properly.

- Enable the Pulseaudio to Jack bridge under `config.yml`

        plugins:
            ...
            ...
            ## Set Pulseaudio apps to sound through by JACK:
            - pulseaudio-jack-sink.py
            ## Enables Pulseaudio to get sound from paired BT devices:
            - pulseaudio-BT.py

- Now your Pulseaudio sources will be available under Jack at ports:

        $ jack_lsp pulse
        pulse_sink:front-left
        pulse_sink:front-right


## Tools:

Checking sound cards usage:

    sudo fuser -v /dev/snd/*

