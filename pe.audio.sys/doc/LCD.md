# LCD for pre.di.c

<a href="url"><img src="https://github.com/Rsantct/pre.di.c/blob/master/pre.di.c/clients/lcd/images/lcd%20display%20v0.1.jpg" align="center" width="340" ></a>

# Get the LCD hardware

See here:
https://github.com/AudioHumLab/FIRtro/wiki/855-Display-LCD


# The software

`lcdproc` versions 0.5.6 and 0.5.7 works with the *usb4all* driver, but newer Debian packaged versions does not.

So it is necessary to download **0.5.7** from sourceforge and manually compile.

https://sourceforge.net/projects/lcdproc/files/

    ./configure --prefix=/usr/local --enable-drivers=hd44780
    make
    sudo make install

Above will install lcdproc under `/usr/local` then you need to point to that location under `pe.audio.sys/share/scripts/lcd/LCDd.conf`:

    DriverPath=/usr/local/lib/lcdproc/

## usb4all needs USB permissions

Prepare `/etc/udev/rules.d/50-usb.rules`

    # allow access to usb devices for users in dialout group
    SUBSYSTEM=="usb", MODE="0666", GROUP="dialout"

And include your user into the `dialout` group:

    sudo usermod -G dialout -a predic

**Reboot the machine**

## Testing the LCD

(i) Please edit and uncomment the appropiate driver line for your machine arch:

    $ nano pe.audio.sys/share/scripts/lcd/LCDd.conf

Try to start the server:

    $ LCDd -c pe.audio.sys/share/scripts/lcd/LCDd.conf

Test the standard packaged client:

    $ lcdproc -f  &
    
    $ killall lcdproc      # to stop the show

## Enabling pe.audio.sys info to be displayed on the LDC

Enable a `- lcd.py` under the `scripts` section at `config.yml`.
