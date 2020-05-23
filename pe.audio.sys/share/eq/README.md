Drop here the needed files for adjusting bass, treble, loudness contour and target house curves that will be loaded into the Brutefir's EQ stage

More details here:

https://github.com/AudioHumLab/pe.audio.sys/tree/master/pe.audio.sys#the-shareeq-folder

You can find sample files into `share/eq.sample.R20_ext` that comes from the FIRtro and predic projects.

You can make your own EQ curves by running the tools provided here:

https://github.com/AudioHumLab/audiotools/tree/master/brutefir_eq

Just remember to adapt the **`eq:`** section of your speaker's **`brutefir_config`** file accordingly. 

The `bands:` center frequencies list under that section must match the ones from the file **`share/eq/xxxxfreq.dat`**
