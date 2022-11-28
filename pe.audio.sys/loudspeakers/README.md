We provide some loudspeaker folders as examples.


### full_range

The full range folder is very simple, only DRC files are provided. 

No filtering will be applied over the only XO section inside the convolver file `brutefir_config`.

This is the loudspeaker folder used inside the provided `pe.audio.sys/config.yml.sample` and `pe.audio.sys/.state.sample` files.


### 2_ways

This is a slightly advanced loudspeaker configuration. Two ways will be filtered by the convolver file `brutefir_config`.

Accordingly, two set of cross over FIR files are provided, both of them are typical 2000 Hz cross over files with a litte of EQ per driver. The 'minpha' set uses typical LR 24 dB/oct slopes. The 'linpha' set uses brickwall slopes at cross over ends.

In addition, an optional **subsonic** filtering is configured by using the provided `subsonic.mp.pcm` and `subsonic.lp.pcm` FIR files. The 'lp' one has flat GD response but adding 46 ms of extra latency. FIRs are 4096 taps lenght @44100 in order to ensure enough resolution for a 2nd order 30 Hz hi-pass response.


### Convolver performance test (3_way_test)

A dummy "cpu convolution test" configuration, it simulates a 3 WAY XOVER and DRC convolution system over a simple stereo output sound card.

