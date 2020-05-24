Drop here the needed files for adjusting bass, treble, loudness contour and target house curves that will be loaded into the Brutefir's EQ stage

More details here:

https://github.com/AudioHumLab/pe.audio.sys/tree/master/pe.audio.sys#the-shareeq-folder

You can find sample files:

- `share/eq.sample.R20_audiotools/` from the `audiotools` project. Loudness contour curves here span from 0 to 90 phon. Tone curves and room gain house curve have a 1st order slope.

- `share/eq.sample.R20_ext/` from the `FIRtro` and `pre.di.c` projects by the pioneer @rripio. Loudness contour curves here span from 70 to 90 phon. Tone curves and room gain house curve have a 2nd order slope.

You can make your own EQ curves by running the tools provided here:

https://github.com/AudioHumLab/audiotools/tree/master/brutefir_eq

Just remember to adapt the **`eq:`** section of your speaker's **`brutefir_config`** file accordingly. 

The `bands:` center frequencies list under that section must match the ones from the file **`share/eq/xxxxfreq.dat`**

A simple tool is available here:

https://github.com/AudioHumLab/audiotools/tree/master/brutefir_eq#bf_config_logicpy
