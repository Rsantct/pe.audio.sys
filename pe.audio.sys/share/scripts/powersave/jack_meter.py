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

""" A simple jack meter
"""
import sys
import os
import argparse
import numpy as np
import queue
# Thanks to https://python-sounddevice.readthedocs.io
import sounddevice as sd

UHOME           = os.path.expanduser("~")
MAINFOLDER      = f'{UHOME}/pe.audio.sys'


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


def parse_cmdline():

    parser = argparse.ArgumentParser(description=__doc__,
              formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-l', '--list-devices', action='store_true',
            help='list audio devices and exit')

    parser.add_argument('-id', '--input_device', type=int_or_str,
            default='pre_in_loop',
            help='input device (numeric ID or substring, see -l)')

    parser.add_argument('-m', '--mode', type=str,
            default='rms',
            help='\'rms\' or \'peak\'')

    parser.add_argument('-p', '--print', action="store_true",
            default=False,
            help='console print out measured level')

    args = parser.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)

    return args


def main():
    # Main loop: open a capture stream that process audio blocks


    def callback(indata, frames, time, status):
        """ The handler for input stream audio chunks """
        if status:
            print( f'----- {status} -----' )
        qIn.put( indata )


    def measure(b, mode=args.mode):

        if mode == 'rms':
            # Mean square calculation for audio (b)locks
            msqL = np.sum( np.square( b[:,0] ) ) / (fs * dur)
            msqR = np.sum( np.square( b[:,1] ) ) / (fs * dur)
            # Stereo
            if msqL or msqR:    # avoid log10(0+0)
                M = 20 * np.log10(msqL + msqR) / 2.0
            else:
                M = -100.0

        elif mode == 'peak':

            ML, MR = np.max(b[:,0]), np.max(b[:,1])
            M = max(ML, MR)
            M = 20 * np.log10(M)

        else:
            print('bad mode')
            sys.exit()

        return M


    h1 = f'-60       -50       -40       -30       -20       -10        0 {args.mode}'
    h2 =  ' |         |         |         |         |         |         |'
    if args.print:
        print(h1)
        print(h2)

    # Prepare an internal FIFO queue for the callback function
    qIn    = queue.Queue()

    # Getting current Fs
    fs = sd.query_devices(args.input_device, 'input')['default_samplerate']

    # Audio block duration in seconds
    dur = 0.100
    # lenght in samples of the audio block
    bs  = int( fs * dur )

    with sd.InputStream( device=args.input_device,
                          callback   = callback,
                          blocksize  = bs,
                          samplerate = fs,
                          channels   = 2,
                          dither_off = True):
        while True:
            # Reading captured (b)locks:
            b = qIn.get()
            # Compute the measured level
            M = measure(b)
            # Print a nice bar meter
            if args.print:
                M = round(M,1)
                I = max(-60, int(M))
                print( f' {"#" * (60-(-I))}{" " * (-I)}  {M}', end='\r')



if __name__ == '__main__':

    # Reading command line args
    args = parse_cmdline()

    main()
