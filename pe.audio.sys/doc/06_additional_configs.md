## ALSA backended players

If you plan to use ALSA backended players, e.g. librespot, remember to configure properly your **`/.asoundrc`** file.

You can simply copy the provided one `.asoundrc.sample`



## Mouse volume daemon

The user must belong to the system group wich can access to devices under `/dev/input` folder. This group is defined inside `/etc/udev/rules.d/99-input.rules`, it can be seen also this way:

    $ ls -l /dev/input/
    total 0
    crw-rw---- 1 root input 13, 64 Mar 19 20:53 event0
    crw-rw---- 1 root input 13, 63 Mar 19 20:53 mice
    crw-rw---- 1 root input 13, 32 Mar 19 20:53 mouse0

On the above example it can be seen that the group is 'input', so in order to mouse volume daemon to work you need to run:

    $ sudo adduser  paudio  input
  
