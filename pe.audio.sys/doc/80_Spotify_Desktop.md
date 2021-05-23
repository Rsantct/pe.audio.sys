# Spotify Desktop Client (official)

Running the official client is the preferred option, because it provides complete metatada and playback status information.

You need a Linux amd64 machine (PC/Mac), but ARM is not still supported :-/

- Download Spotify Desktop client following instructions from the official site:

https://www.spotify.com/es/download/linux/

        --> Install via command line

            ---> Debian/Ubuntu


- Settings inside **`config.yml`**:

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
