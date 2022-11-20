# Startup add-ons: `plugins`

This folder holds optionals plugin scripts that **can be loaded** on startup when calling `pe.audio.sys/start.py all`

Please see the provided **`config.yml.sample`** file for more info on plugins features.

To enable your plugins, you simply need to put the plugin filename under your **`config.yml`**'s `plugins` section, for instance:

    plugins:
        - mpd.py
        - CDDA.py
        - autoplay_cdda.py

Some plugins can have a subfolder to hold its own code, depending on their complexity.

Plugins's command line usage is simple:

    ~$ plugin_name.py   start | stop
