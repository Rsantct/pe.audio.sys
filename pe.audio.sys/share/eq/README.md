## `eq/`

Drop here the needed files for adjusting bass, treble, loudness contour and target room house curves that will be loaded into the Brutefir's EQ stage.

Find them here:

**`share/eq.sample.R20_audiotools/`**

For more details see here:

[60_system files.md](../../doc/60_system%20files.md)


**IMPORTANT:**

The `"eq"` section on your `brutefir_config` file **must match** the same frequency bands as inside the `share/eq/freq.dat` file.

A simple tool is available here:

https://github.com/AudioHumLab/audiotools/tree/master/brutefir_eq#bf_config_logic.py

## `eq/samplerate/`

Additional general purpose pcm filters, for example SUBSONIC.

Use `bin/peaudiosys_make_brutefir_config.py` to properly configure your `brutefir_config`
