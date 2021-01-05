
### Install Pulseaudio

    sudo apt install    pulseaudio pulseaudio-utils pavucontrol \
                        pulseaudio-module-bluetooth pulseaudio-module-jack


### Checking sound cards usage:

    sudo fuser -v /dev/snd/*

### Checking Pulseaudio services (systemd)

    ```
    systemctl        status pulseaudio      # system wide scope
    systemctl --user status pulseaudio      # user scope
    ```

- Enable Pulseadio for your user:

    ```
    systemctl --user enable pulseaudio
    systemctl --user start pulseaudio
    ```
    
- Disable the system wide service if necessary
    
    ```
    systemctl  stop    pulseaudio
    systemctl  disable pulseaudio
    ```

- pe.audio.sys will automatically ask Pulseaudio to release the sound card to run Jack properly.

- Enable the Pulseaudio to Jack bridge under `pe.audio.sys/config.yml`

    ```
    scripts:
        ...
        ...
        ## Set Pulseaudio apps to sound through by JACK:
        - pulseaudio-jack-sink.py
        ## Enables Pulseaudio to get sound from paired BT devices:
        - pulseaudio-BT.py
    ```

- Now your Pulseaudio sources will be available under Jack at ports:

    ```
    $ jack_lsp pulse
    pulse_sink:front-left
    pulse_sink:front-right
    ```
