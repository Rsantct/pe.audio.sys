# System performance

**Convolution** filtering is a **high CPU demanding** task.

If you want watching movies and video with **minimal audio latency** (say less than 100 ms), you need a powerfull CPU and tuning your system accordingly.

## loudspeakers/3_way_test

The file `loudspeakers/3_way_test/brutefir_config` is intended for you to test your system performance capability.

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

In a different way, latency is naturally implicit when using linear phase FIR, this is not a processing issue, but a inherit property of linear phase filters because if its own nature.

### Testing system latency

Run JACK and Brutefir alone, without the whole pe.audio.sys scripts. 

***(PLEASE switch-off your AMPLIFIER or jack_disconnect system:playback_X)***

<a href="url"><img src="https://github.com/Rsantct/pe.audio.sys/blob/master/pe.audio.sys/doc/images/testing_latency.png" align="center" width="800" ></a>

Play trial and error with JACK **`--period xxx`**. Choose a power of 2 value, and equal or smaller than the `brutefir_config` **partition size**.

Some times Jack_period == brutefir_partition_size gets the best results

For serial interfacing USB/Firewire/I2S sound cards use **`-n 3`**.

For instance, having a Brutefir partion size of 2048 (`filter_length: 2048,8;  # 16K taps`):

    # Tested in a old Mac Mini mid 2007; Intel Core 2 CPU @ 2.00GHz
    # CPU overall loading is about 40%

    cd            ~/pe.audio.sys/loudspeakers/3_way_test

    # JACK period = 1024
    jackd         -R -L 2 -d alsa -d hw:0 -r 44100 --period 1024 -n 2 &
    brutefir      brutefir_config &
    jack_connect  brutefir:fr.L loopback:playback_1
    jack_delay    -O brutefir:in.L   -I loopback:capture_1
            4096.002 frames   92.880 ms
            ...

    killall brutefir jackd

    # JACK period = 2048
    jackd         -R -L 2 -d alsa -d hw:0 -r 44100 --period 2048 -n 2 &
    brutefir      brutefir_config &
    jack_connect  brutefir:fr.L loopback:playback_1
    jack_delay    -O brutefir:in.L   -I loopback:capture_1
            3072.001 frames   69.660 ms
            ...


These are not too bad results, even for watching to movies and videos.


Same results can be obtained by using a **Rapspberry Pi 3** with the same configuration, but CPU% loading reaches >65%, wich is near the dangeous limit and you will probably have no CPU headroom to run MPD and other stuff..., but leaving Brutefir partitioning you can get ride off.

Anyway a Raspberry Pi 3 is not a good option for 3 way XOVER filtering + DRC, but 2 way + DRC works fine.

Better latencies can be obtained by using a modern powerful CPU and lower Jack --period and Brutefir partition size values.
