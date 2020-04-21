# Startup add-ons: scripts

This folder holds optionals scripts that **can be loaded** on startup when calling `pe.audio.sys/start.py all`

Please see the provided **`config.yml.sample`** file for more info on scripts features.

To enable your needed scripts, you simply need to put the script filename under your **`config.yml`**'s `scripts` section, for instance:

    scripts:
        - mpd.py
        - CDDA.py
        - autoplay_cdda.py

Some scripts can have a subfolder to hold its own code, depending on their complexity.

Script's command line usage is simple:

    ~$ script_name.py   start | stop
