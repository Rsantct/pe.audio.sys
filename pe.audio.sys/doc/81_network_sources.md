## Network sources: JackTrip

https://www.jacktrip.com

You can send audio from another PC over the same LAN.

### Local pe.audio.sys

Example:

    pe.audio.sys/config/config.yml
    
        sources:
    
            MacBook Pro:
                jack_pname:      MacBook Pro
                jacktrip:        true            # This triggers the launch of the jacktrip server


### Remote Mac as remote source

#### You need to install:

- JackTrip (go to the offcial site to download the macOS installer)
- [BlackHole](https://github.com/ExistentialAudio/BlackHole) to route your audio. Please do not use the Homebrew installation method currently does not work, install it by downloading the [official package](https://existential.audio/blackhole).

In order to automatically switch the Mac system-wide audio playback to the pAudio BlackHole input, and restore later, you may want to install a couple of additional tools:

- [AdjustVolume](https://github.com/jonomuller/device-volume-adjuster) This is comes as a ZIP file. Copy to `/usr/local/bin/` or just to `$HOME/bin/`
- [SwitchAudioSource](https://github.com/deweller/switchaudio-osx) This installs via Homebrew, If you still don’t have Homebrew, please go to https://brew.sh

NOTICE:
To alow the binary **AdjustVolume** to be executed, you'll need to unblock it, open a terminal and run:

    xattr -d com.apple.quarantine ~/bin/AdjustVolume

#### Sending audio to pe.audio.sys

Just run the provided script **`bin/paudio_macos_cli.sh`**

```
    $ paudio_macos_cli.sh --help
    
        Enviador de audio por LAN basado en JackTrip.
    
            Cambia la salida del escritorio a "BlackHole 2ch" y ejecuta JackTrip
            capturando el audio de BlackHole y enviándolo al HOST_REMOTO
    
        Uso:
    
            iniciar:    paudio_macos_cli.sh   HOST_REMOTO [SAMPLE_RATE]
            detener:    paudio_macos_cli.sh   stop (restaura la salida de sonido del escritorio)
```    
