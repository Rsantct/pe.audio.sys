#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.
#
# 'pe.audio.sys' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'pe.audio.sys' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.

"""
    A pe.audio.sys daemon to autoplay a CD-Audio when inserted

    Usage:  autoplay_cdda.py  start | stop  &
"""

# To check your devices from command line:
# $ udevadm monitor
# ... ...
# UDEV  [5336.857159] change   /devices/pci0000:00/0000:00:1f.1/ata1/host0/target0:0:0/0:0:0:0/block/sr0 (block)
# UDEV  [5358.454256] change   /devices/pci0000:00/0000:00:1d.7/usb5/5-6/5-6:1.0/host4/target4:0:0/4:0:0:0/block/sr1 (block)


# Some distros as Ubuntu 18.04 LTS doesn't have
# libcdio-dev >=2.0 as required from pycdio.
#import cdio, pycdio
# (i) pycdio dependencies:
#       python-dev libcdio-dev libiso9660-dev swig pkg-config
# Workaround: lets use 'cdinfo' from 'cdtool' package (cdrom command line tools)

import  os
import  sys
from    time import sleep
import  pyudev
from    subprocess import check_output, Popen
from    json import loads as json_loads

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys')

from share.miscel                       import send_cmd
from share.services.players_mod.cdda    import save_disc_metadata

ME = 'autoplay_cdda'

# OPTIONAL USER CONFIG
USE_CD_MACRO = False


def find_cd_macro():
    """ Looks for a macro named 'NN_cd' or similar, if not found
        then returns a fake macro name.
    """
    result = '-'    # a fake macro name
    mNames = json_loads( send_cmd( 'aux get_macros' ) )
    for mName in mNames:
        if '_cd' in mName.lower():
            result = mName
            break
    return result


def check_for_CDDA(d):

    srDevice = d.device_path.split('/')[-1]
    CDROM = f'/dev/{srDevice}'

    def autoplay_CDDA():

        cd_macro_found = False

        if USE_CD_MACRO:
            mName = find_cd_macro()
            if mName == '-':
                cd_macro_found = True
                send_cmd( f'aux run_macro {mName}' )

        if not cd_macro_found:
            send_cmd( 'player pause', sender=ME, verbose=True )
            send_cmd( 'aux warning clear', sender=ME, verbose=True, timeout=1 )
            send_cmd( 'aux warning set disc loading ...', sender=ME, verbose=True, timeout=1 )
            send_cmd( 'aux warning expire 10', sender=ME, verbose=True, timeout=1 )
            send_cmd( 'preamp input cd', sender=ME, verbose=True )
            sleep(.5)
            # (!) Ordering 'play' will BLOCK the server while
            #     waiting for the disc to be loaded
            send_cmd( 'player play',                      sender=ME, verbose=True )


    # Verbose if not CDDA detected
    try:
        # $ cdinfo -a # will output: no_disc | data_disc | xx:xx.xx
        tmp = check_output( f'cdinfo -a -d {CDROM}'.split() ).decode().strip()

        if ':' in tmp:
            print( f'(autoplay_cdda) trying to play the CD Audio disk' )
            # autoplay the disc
            autoplay_CDDA()

        elif 'no_disc' in tmp:
            print( f'(autoplay_cdda) no disc' )
            # flushing .cdda_info
            save_disc_metadata()

        elif 'data_disc' in tmp:
            print( f'(autoplay_cdda) data disc' )
            # flushing .cdda_info
            save_disc_metadata()

    except:
        print( f'(autoplay_cdda) This script needs \'cdtool\' (command line cdrom tool)' )


def stop():
    Popen( f'pkill -KILL -f autoplay_cdda'.split() )
    sleep(.5)


def main():
    # Main observer daemon
    context = pyudev.Context()
    umonitor = pyudev.Monitor.from_netlink(context)
    umonitor.filter_by(subsystem='block', device_type='disk')
    uobserver = pyudev.MonitorObserver( umonitor, callback=check_for_CDDA )
    uobserver.daemon = False  # set False will block the process when started.
    uobserver.start()


if __name__ == '__main__':

    if sys.argv[1:]:
        if sys.argv[1] == 'start':
            main()
        elif sys.argv[1] == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)
