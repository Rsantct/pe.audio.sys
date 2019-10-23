#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
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
  Calculates target curves to in room EQ a loudspeaker system,
  and plots graphs of them.

  Usage:
  
    peaudiosys_do_target.py  -rXX -cXX -hXX

        -rXX    romm_gain    of XX dB
        -cXX    house_corner at XX Hz
        -hXX    house_atten  of XX dB
"""

import sys, os
import numpy as np
import curves

UHOME = os.path.expanduser("~")
sys.path.append( f'{UHOME}/pe.audio.sys/share' )
from core import EQ_CURVES 

def do_plot():
    # notice freq is already log spaced
    # and mag is in dB
    fig = plt.figure()
    fig.subplots_adjust(hspace=.5)
    ax0 = fig.add_subplot(211)
    ax0.set_ylim(-3, 9)
    ax0.semilogx(freq, eq_mag)
    ax0.set_title("mag (dB)")
    ax1 = fig.add_subplot(212)
    ax1.set_ylim(-.5, .5)
    ax1.semilogx(freq, eq_pha * np.pi / 180)
    ax1.set_title("pha (deg)")
    plt.show()

if __name__ == '__main__':

    # Prepare output folder
    OUTPUT_FOLDER = f'{UHOME}/tmp/target_curves'
    try:
        os.mkdir( f'{UHOME}/tmp')
    except:
        pass
    try:
        os.mkdir( OUTPUT_FOLDER )
    except:
        pass

    # Read target parameteres from command line
    room_gain, house_corner, house_atten = None, None, None
    try:
        for opc in sys.argv[1:]:
            if opc[:2] == '-r':
                room_gain    = float( opc[2:] )
            if opc[:2] == '-c':
                house_corner = float( opc[2:] )
            if opc[:2] == '-h':
                house_atten  = float( opc[2:] )
    except:
        print(__doc__)
        exit()

    if not all( (room_gain, house_corner, house_atten) ):
        print(__doc__)
        exit()

    # Filenames suffixed with the room and house dBs ;-)
    suffix = '+' + str(round(room_gain, 1)) + '-' + str(round(house_atten, 1))
    target_mag_path = f'{OUTPUT_FOLDER}/target_mag_{suffix}.dat'
    target_pha_path = f'{OUTPUT_FOLDER}/target_pha_{suffix}.dat'

    # Prepare target curve
    freq   = EQ_CURVES['freqs']
    eq_mag = np.zeros(len(freq))

    if house_atten > 0:
        house = curves.HouseCurve( freq, house_corner, house_atten )
    else:
        house = np.zeros( len(freq) )
    room = curves.RoomGain( freq, room_gain )

    # Compose magnitudes
    eq_mag = eq_mag + house + room

    # Derive the phase ( notice mag is in dB )
    try:
        from scipy.signal import hilbert
        eq_pha = np.angle( ( hilbert( np.abs( 10**(eq_mag/20) ) ) ) )    
    # if you have not scipy signal installed, you can just use zeros:
    except:
        eq_pha = np.zeros(len(freq))

    # Write data to file
    np.savetxt (target_mag_path, eq_mag)
    np.savetxt (target_pha_path, eq_pha)
    print( f'Target curves stored at:\n{target_mag_path}\n{target_pha_path}' )

    try:
        import matplotlib.pyplot as plt
        do_plot()
    except:
        print ( 'cannot plot, please install \'matplotlib\' and \'tk\' for Python3' )
