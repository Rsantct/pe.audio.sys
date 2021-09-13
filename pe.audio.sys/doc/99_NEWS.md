
## December 18, 2020: version 1.0 released

- `share/eq/*.dat` multicurve files has changed its internal arrangement
- Equal loudness related commands and parameters has changed

See the `doc/` folder for detailed information about this.

**PLEASE UPDATE:**

- your `share/eq/*.dat` multicurve files with the new ones
  provided under `share/eq/eq.sample.R20_audiotools/`

    ```
    bass_mag.dat
    bass_pha.dat
    treble_mag.dat
    treble_pha.dat
    ref_XX_loudness_mag.dat
    ref_XX_loudness_pha.dat
    ```
    
- your `config.yml`:

    ```
                        refSPL=XX       (new item)
    loud_ceil       --> eq_loud_ceil
    loudness_track  --> equal_loudness
    ```

- your `.state.yml`:

    ```
    loudness_track:  --> equal_loudness: true|false
    loudness_ref:    --> lu_offset: XX
    ```

- your `macros/` files if them issue any loudness command


## Jan 2021, version 1.0a

- New script `zita_link.py`, a LAN one-to-one audio receiver based on zita-njbridge from Fons Adriaensen, replaces former zita multicast versions, for 'remote' sources usage.

- New Bluetooth receiver: `script/pulseaudio-BT.py` and related doc/ and macros to listen to Bluetooth sources.

- New `script/node_web_server.py` replaces calling node from /etc/rc.local

- Some fixes and documentation.


## May 2021, version 1.0b

- New documentation for remote pe.audio.sys sources listening.
- New Firewire Audio Interfaces support.

## Sep 2012, version 1.0c

- New subsonic filtering feature.
