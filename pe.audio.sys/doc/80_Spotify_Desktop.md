# Spotify Desktop Client (official)

Running the official client is the preferred option, because it provides complete metatada and playback status information.

You need a Linux amd64 machine (PC/Mac), but ARM is not still supported :-/

## Download and log in

Download Spotify Desktop client following instructions from the official site:

https://www.spotify.com/es/download/linux/

        --> Install via command line

            ---> Debian/Ubuntu

First time you need to connect a keyboard and mouse, then login with your credentials.

Later, you can consider a 'headless' Desktop system, by auto login on your desktop, see below.

### Limit the disk cache size

The Linux client may consume a lot of disk space for storing cache, and currently the configuration interface only offers clearing the cache.

For 1 Gb limit, add the following line in **`/home/$USER/snap/spotify/current/.config/spotify/prefs`**

        storage.size=1024

If you installed Spotify in Ubuntu via apititude, the config file is `~/.var/app/com.spotify.Client/config/spotify/prefs`


## pe.audio.sys configuration

Settings inside **`config.yml`**:

- configure the `spotify`source
- enable `pulseaudio-jack-sink.py` and `spotify_monitor.py` plugins

```
sources:
    ...
    ...
    spotify:
        gain:           0.0
        jack_pname:     pulse_sink


plugins:
    ...
    ...
    - pulseaudio-jack-sink.py
    - spotify_monitor.py        #  gets metadata an playback status
```

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



