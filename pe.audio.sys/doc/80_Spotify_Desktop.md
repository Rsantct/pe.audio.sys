# Spotify Desktop Client (official)

Running the official client is the preferred option, because it provides complete metatada and playback status information.

You need a Linux amd64 machine (PC/Mac), but ARM is not still supported :-/

## Download and logging account

Download Spotify Desktop client following instructions from the official site:

https://www.spotify.com/es/download/linux/

        --> Install via command line

            ---> Debian/Ubuntu

First time you need to connect a keyboard and mouse, then login with your credentials.


### Autostart Spotify for `paudio` session

Prepare a desktop autostart file:

    /home/paudio/.config/autostart/spotify.desktop 

                [Desktop Entry]
                Type=Application
                Exec=spotify
                Hidden=false
                NoDisplay=false
                X-GNOME-Autostart-enabled=true
                Name[es_ES]=spotify
                Name=spotify
                Comment[es_ES]=
                Comment=

### Autologin `paudio` user session on Desktop

(i) If you want this, **please consider remove `paudio` from the `sudo` group**


    /etc/gdm3/daemon.conf 

            [daemon]
                AutomaticLoginEnable = true
                AutomaticLogin = paudio





## pe.audio.sys configuration

Settings inside **`config.yml`**:

- configure the `spotify`source 
- enable `pulseaudio-jack-sink.py` and `spotify_monitor.py` scripts

```
sources:
    ...
    ...
    spotify:
        gain:           0.0
        capture_port:   pulse_sink


scripts:
    ...
    ...
    - pulseaudio-jack-sink.py
    - spotify_monitor.py        #  gets metadata an playback status
```
