# System performance

**Convolution** filtering is a **high CPU demanding** task.

If you want watching movies and video with **minimal audio latency** (say less than 100 ms), you need a powerfull CPU and tuning your system accordingly.

## loudspeakers/3_way_test

The file `loudspeakers/3_way_test/brutefir_config` is intended for you to test your system performance.

It simulates a 3 WAY XOVER and DRC convolution system over a simple stereo output sound card


                                                /--> f.hi.L >--\
                                               /                \
    --> in.L >----> f.eq.L >----> f.drc.L >---X----> f.mi.L >----X---> fr.L
                                               \                /
                                                \--> f.lo.L >--/

    --> in.R >-- ... ... ... ... ... ... the same as L ... ... ... --> fr.R


See on Brutefir's doc about tuning number of partitions, bit depth and dither:

https://torger.se/anders/brutefir.html#tuning_1

https://torger.se/anders/brutefir.html#tuning_5

https://torger.se/anders/brutefir.html#config_6


## CPU load

**`htop`** displays CPU% usage:

<a href="url"><img src="https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/doc/images/htop.png" align="center" width="600" ></a>


**Qjackctl** displays JACK RT real time index information:

<a href="url"><img src="https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/doc/images/qjackctl_RT_index.png" align="center" width="400" ></a>


**Brutefir** real time index can be obtained by issuing the `rti` command, which is similar to the CPU% load of the Brutefir process:

<a href="url"><img src="https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/doc/images/bf_rti.png" align="center" width="400" ></a>



## System latency

System latency depends on Jack audio buffering --period and --nperiod parameters, xrun drop-offs are the aside effect for too low buffering values.

Latency also depends on convolution partitioning, whith high CPU% load as aside effect.

In a different way, latency is naturally implicit when using linear phase FIR, this is not a processing issue, but a inherit property of lineal phase filters because if its own nature.

### Testing system latency

Run JACK and Brutefir alone, without the whole pe.audio.sys scripts. 

***(PLEASE switch-off your AMPLIFIER or jack_disconnect system:playback_X)***

<a href="url"><img src="https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/doc/images/testing_latency.png" align="center" width="800" ></a>

For instance:

    cd          ~/pe.audio.sys/loudspeakers/3_way_test
    jackd       -R -L 2 -d alsa -d hw:0 -r 44100 --period 1024 -n 2 &
    brutefir    brutefir_config &
    jack        connect brutefir:fr.L loopback:playback_1
    jack_delay  -O brutefir:in.L   -I loopback:capture_1
    
            ...    
            4096.002 frames   92.880 ms
            4096.000 frames   92.880 ms
            ...

Play trial and error with JACK **`--period xxx`**. Choose a power of 2 value, and equal or smaller than the `brutefir_config` **partition size**.

For USB/Firewire sound cards use **`-n 3`**.







