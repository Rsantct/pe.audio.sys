#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A pe.audio.sys daemon to auto eject a CD-Audio when playback is over

    Usage:  auteject_cdda.py  start | stop  &
"""

from    os.path import expanduser
import  sys
import  threading
from    time import sleep, ctime
from    subprocess import Popen

UHOME = expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from    miscel  import  read_state_from_disk, read_metadata_from_disk, \
                        LOG_FOLDER


def main_loop():

    def eject_job(timer=5):
        """ Runs forever every 5 sec:
            - Reads the playback files to detect when a CD disc is over,
              then ejects the disc.
            - Waits the timer
        """

        disc_is_over    = False

        while True:

            md = read_metadata_from_disk()
            if not md:
                continue

            # check if source = 'cd'
            if read_state_from_disk()['input'].lower() == 'cd':

                # check if the track being playe is last one,
                # also avoids bare default metadata
                if md["track_num"] == md["tracks_tot"] and \
                   md["time_tot"][-2:].isdigit()       and \
                   md["time_tot"]   != '00:00':

                    # time_pos could not reach time_tot by ~2 sec :-/
                    if md["time_pos"][3:-1] == md["time_tot"][:-1]:
                        if abs( int(md["time_pos"][-2:]) -
                                int(md["time_tot"][-2:]) )  <= 2:
                            disc_is_over = True


            if disc_is_over:
                tmp = f'{ctime()} tpos: {md["time_pos"]}, ttot: {md["time_tot"]}'
                print(f'(autoeject_cdda) {tmp}')
                with open(logPath, 'a') as f:
                    f.write(f'{tmp}, ejecting disc.\n')
                sleep(2) # courtesy wait
                Popen("peaudiosys_control player eject".split())
                print(f'(autoeject_cdda) CD playback is over, disc ejected.')
                disc_is_over = False

            # sleep timer
            sleep(timer)


    # Thread the job
    job_loop = threading.Thread( target=eject_job, args=() )
    job_loop.start()


def stop():
    Popen( ['pkill', '-KILL', '-f', 'autoeject_cdda.py start'] )
    sleep(.25)


if __name__ == '__main__':

    logPath = f'{LOG_FOLDER}/autoeject_cdda.log'

    if sys.argv[1:]:
        if sys.argv[1] == 'start':
            main_loop()
        elif sys.argv[1] == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)
