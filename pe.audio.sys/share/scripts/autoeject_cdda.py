#!/usr/bin/env python3

# Copyright (c) 2021 Rafael Sánchez
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
    A pe.audio.sys daemon to auto eject a CD-Audio when playback is over

    Usage:  auteject_cdda.py  start | stop  &
"""

from    os.path import expanduser
import  sys
import  threading
from    time import sleep
import  json
import  yaml
from    subprocess import Popen

UHOME = expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'
sys.path.append(MAINFOLDER)

from    share.miscel  import    PLAYER_META_PATH,   \
                                PLAYER_STATE_PATH,  \
                                get_source


def read_state_file():
    with open(PLAYER_STATE_PATH, 'r') as f:
        return f.read()


def read_metadata_file():
    with open(PLAYER_META_PATH, 'r') as f:
        return json.loads( f.read() )


def main_loop():

    def eject_job(timer=5):
        """ Runs forever every 5 sec:
            - Reads the playback files to detect when a CD disc is over,
              then ejects the disc.
            - Waits the timer
        """

        disc_is_over    = False
        tries           = 3     # to ensure that .player_state changes from 'play'

        while True:

            md          = read_metadata_file()
            is_playing  = read_state_file() == 'play'

            if get_source().lower() == 'cd' and is_playing:

                if md["track_num"] == md["tracks_tot"]:

                    # time_pos could not reach time_tot by ~2 sec :-/
                    if md["time_pos"][3:-1] == md["time_tot"][:-1]:
                        if abs( int(md["time_pos"][-2:]) - int(md["time_tot"][-2:])) <= 2:
                            disc_is_over = True
                            tries -= 1
            else:
                tries = 3

            if disc_is_over and not tries:
                Popen("peaudiosys_control player eject".split())
                print(f'(autoeject_cdda.py) CD playback is over, disc ejected.')
                disc_is_over = False

            # SLEEP TIMER
            sleep(timer)


    # Loop forever
    job_loop = threading.Thread( target=eject_job, args=() )
    job_loop.start()



def stop():
    Popen( f'pkill -KILL -f autoeject_cdda'.split() )
    sleep(.5)


if __name__ == '__main__':

    if sys.argv[1:]:
        if sys.argv[1] == 'start':
            main_loop()
        elif sys.argv[1] == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)
