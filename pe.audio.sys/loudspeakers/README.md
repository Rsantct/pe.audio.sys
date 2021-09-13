We provide two loudspeaker folders as examples.


### full_range

The full range folder is very simple, only DRC files are provided. 

No filtering will be applied over the only XO section inside the convolver file `brutefir_config`.

This is the loudspeaker folder used inside the provided `pe.audio.sys/config.yml.sample` and `pe.audio.sys/.state.yml.sample` files.


### 2_ways

This is a slightly advanced loudspeaker configuration. Two ways will be filtered by the convolver file `brutefir_config`.

Accordingly, two set of cross over FIR files are provided, both of them are typical 2000 Hz cross over files with a litte of EQ per driver. The 'minpha' set uses typical LR 24 dB/oct slopes. The 'linpha' set uses brickwall slopes at cross over ends.

In addition, an optional **subsonic** filtering is configured by using the provided `subsonic.mp.pcm` and `subsonic.lp.pcm` FIR files with 4098 taps lenght. The 'lp' one has flat GD response but adding 46 ms of extra latency.


### Convolver performance test (3_way_test)

A dummy "cpu convolution test" configuration, it simulates a 3 WAY XOVER and DRC convolution system over a simple stereo output sound card.

