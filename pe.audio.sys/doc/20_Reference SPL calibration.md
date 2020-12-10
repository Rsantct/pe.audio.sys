# Reference SPL calibration


You'll need:

    - a SPL meter with C curve and slow time integration mode.

    - a track of pink noise -20 dBFS RMS limited to 500-2000 Hz (find it under `doc/test signals` folder).

Full bandwidth noise is not recommended because of issues on bass room modes and/or typical reflections on mid and high frequencies due to room and furnitures.


Preliminary:


1. Check the capability of your loudspeaker + amplifier pairs . Find the one wich has the more compromised performance. Then adjust the rest to match its sensitivity from the point of view of your sound card outputs (analog domain).

2. Adjust your sound card without mixer software attenuation.

3. Check carefully the max gain on each of your xover FIR pcm files. Be aware to set Brutefir attenuations to ensure you will not clip when a near to 0 dBFS signal is processed.

4. As an starting point, set your `config.yml` file:

    ref_level_gain: -10.0


As per discussed here:

https://www.soundonsound.com/techniques/establishing-project-studio-reference-monitoring-levels#

We propose as a summary:

5. Decide your Reference SPL as per your listening room volume:

            Room Volume m3          Ref. SPL

            > 566                   83 dBC

            284 - 566               80 dBC

            143 - 283               78 dBC

            42 - 142                76 dBC  <---- most domestic rooms

            < 42                    74 dBC

Excerpt from [soundandsound article](https://www.soundonsound.com/techniques/establishing-project-studio-reference-monitoring-levels?page=2) (page 2):


*However, although this 83dB SPL reference level (with 103dB peaks) is perfectly acceptable when listening in a big space, like a cinema or a film dubbing theatre, or even a very large and well‑treated commercial studio control room, it will be completely overwhelming in a smaller space, because the listener is inevitably sitting much closer to both the speakers and the room boundaries. The very different nature of early reflections in these conditions makes the level seem, psychoacoustically, much higher than it would be in a larger room.*

*Consequently, the optimum reference level for smaller rooms needs to be significantly lower, on a scale which is dependent on the enclosed volume of the room in question.*



6. Ensure pe.audio.sys has not any running eq:

    ```
    level:          -20
    loudness_ref:   0
    loudness_trak:  off
    drc:            none, or the one you have prepared (*)
    bass:           0
    treble:         0
    target:         not much relevant, but none is preferred.
    ```

(*) *It is supposed that your DRC pcm FIR has been referenced on your mid frequency region from your listening position averaged response.* 


7. Play the mid band limited pink noise track on the LEFT channel loudspeaker.

8. Adjust pe.audio.sys level until the SPL meter displays ~ 76.0 dBC  at your listening position.

(i) If you cannot reach 76 dBC at listening point, set `ref_level_gain: 0.0` inside `config.yml`, restart pe.audio.sys and try it again. Maybe your analog gear needs more gain or maybe your sound card out line level is too low.

9. Calculate the appropriate `ref_level_gain` to get 76 dBC for level=0 and set it inside `config.yml`. 

Restart pe.audio.sys.

10. Repeat on RIGTH loudspeaker, if your channels are balanced, you will get the same 76 dBC at level=0.

Almost done ...

11. In order to get the best digital S/N ratio, if your `ref_level_gain` value goes too low, it is prefereable to insert analog attenuation from your sound card outputs, that way your `ref_level_gain` will be not much away from 0 dB then you get the best S/N ratio ;-)

Be advised: from now on your gain headroom will be ceiled as per the new `ref_level_gain`. If for some reason this is not enough for you, the only option is to reduce the digital gain chain by setting `ref_level_gain` for instance at -6.0 dB, then add +6.0 dB of analog gain on your analog gear.

## Testing whith real music:

Bob Katz has published a very helpful list of CD references classified as per its loudness strength.

https://www.digido.com/honor-roll/

Recordings are grouped into four categories, as per how much you need to put down your calibrated volume control in order to maintain the perceived loudness when listening to.

Some examples are:

    + 0 dB
    Reunion at Carnegie Hall – The Weavers
    Heartattack And Vine - Tom Waits

    - 9 dB
    Brand New Day – Sting

In addition, the pe.audio.sys "LU monitor" display bar will show the loudness strenght of these recordings.

Regarding this, pe.audio.sys provides the "LU offset" control slider, for you to compensate your calibrated listening level when playing intrensically high loudness recordings. Just put the slider in a position matching the "LU meter" bar displacement.

## Listening at moderate or low volume.

All discussed above refers to normal (reference) listening volume.

For low volume listening, the LOUDNESS control switch will help you.

In order to correctly apply a loudness compensantion curve, you'll need to adjust properly the LU offset control slider as discussed above.

The default `config.yml` file indicates:

    # Estimated perceived reference SPL at listening point
    refSPL:         83

So from the loudness compensation curves provided under the `pe.audio.sys/share/eq` folder, it will be used the  **`ref_83_loudness...dat`** ones.

*Although this may seem inconsistent with your calibrated 76 dBC system, that's fine. This is because the subjective room volume compensation applied will cause you to perceive the standard reference SPL as if you were inside a large venue, as explained above.*
 
When your level control is properly calibrated, you'll find that you can safely keep loudness compensation activated in pe.audio.sys. Then, when you listen to some ""loudness war"" recording, you don't need to readjust your level control, instead you can adjust the LU offset control to compensate for that strong recording.






