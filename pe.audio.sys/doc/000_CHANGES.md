## This fork main changes and features

### 2019 works in progress

* Splitting the mplayer related scripts, i.e. `DVB` and `istreams`, to leave a start/stop script under the `init` folder and a separate on the fly control script under `clients/bin`.

### 2019-Feb

* Web control playback buttons upgraded with 'rewind' and 'fast forward'. Useful when you want to move along a high lenght track, for example some internet radio podcast. Also useful for MPD navigate. Spotify Desktop also included on playback buttons operation.

### 2019-Jan:

* Recovered the LCD display from FIRtro: `init/lcd`, `clients/lcd/...`

* A volume control by using a mouse has been introduced. A new parameter `alert_level` can be set inside `config/config.yml`.

* Control web page enhancements:

   * A basic view by default, a new gear button will display advanced controls.

   * When [istreams] input, a link button allows the user to enter or paste a stream url to be played.

   * If available metadata, the page will show the audio bitrate and the time track info.

* If your pre.di.c machine uses a Spotify desktop client, full metadata info will be displayed under the control web page.

* Minor changes on run level options into `stopaudio.py` and `startaudio.py`.

* Minor code mod under `startaudio.py` to able Jack to run under Pulseaudio desktop machines.

* Minor code mod under `start_pid()` at `predic.py` to able processes (e.g. mplayer) to redirect his stdout and stderr to a file that could be read later from others process.

* `DVB.py` has been rewritten, see below.

* New server mechanism, see below.

* Code arrangement ( issue #29 ), including:

    * `scripts` folder renamed to `init`
    * scripts inside the `init` folder leaving the `.py` or `.sh` extension.
    * `mpd_load.py` renamed to `mpd`
    * updating the install script `.install/update_predic.sh`


```
$HOME/
  │    
  ├── bin/     (user bin folder including some pre.di.c tools)
  │    
  ├── pre.di.c/
      │
      ├── cdda_fifo   dvb_fifo    istreams_fifo
      │
      ├── bin
      │   │   basepaths.py    peq_control.py  startaudio.py
      │   └── control.py      predic.py       stopaudio.py
      │       getconfigs.py   server.py
      │
      ├── init
      │   └── alsa_loop       mpd     ...     ...
      │
      ├── clients
      │   │
      │   ├── bin
      │   │   └── aux         players         mouse_volume     ...
      │   │
      │   ├── macros
      │   │   └── 1_RNE       2_R.Clasica     ...     ...
      │   │
      │   └── www   (the web page, server side and client side code)
```

## New server

It has been rewritten the `server.py` code in order to leave it as a general purpose server script that can run specific service modules.

The most important service is the one supported by the **`control.py`** module (formerly `server_process.py`).

This way the server can runs also other general interest service modules.

So, if we wanna run the server that will listen for pre.di.c management, we run:

    server.py control

If wanna run another server for auxiliary tasks:

    server.py aux

The arguments `control` or `aux` will indicates to `server.py` to IMPORT these module names to work.

Any service module intended to be used under `server.py` must provide an interfacing function named `do()`.

The addresses and ports mapping to run each service are specified under `config/config.yml`.

Also, an optimization has been done regarding the original `server.py` mechanism: it has been omitted the status dict when calling `process_commands()` because status is already read by default when calling this function.

## DVB script

    Usage:   DVB        start  [ <preset_num> | <channel_name> ]
                        stop
                        prev  (load previous from recent presets)
                        preset <preset_num>
                        name   <channel_name>

Now `DVB` uses a unique `config/DVB-T.yml` file for user presets configuration and also for recent used presets to be persistent, so `config/DVB-T_state.yml` is not used anymore.

The YAML parser now is `ruamer.yaml` that preserves comments and the order of yaml items when dumping.

## INSTALL scripts

Install and update scripts are provided to easy local machine maintenance and updating.
