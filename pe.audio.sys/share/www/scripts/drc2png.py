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


""" usage:      drc2png.py  <loudspeaker_name> [--quiet]
"""

import sys
import os
UHOME = os.path.expanduser("~")
import numpy as np
from scipy import signal
from matplotlib import pyplot as plt
import yaml

RGBweb = (.15, .15, .15)

def readPCM32(fname):
    """ reads impulse from a pcm float32 file
    """
    #return np.fromfile(fname, dtype='float32')
    return np.memmap(fname, dtype='float32', mode='r')

def get_spectrum(imp, fs):
    fNyq = fs / 2.0
    # Semispectrum (whole=False -->  w to Nyquist)
    w, h = signal.freqz(imp, worN=int(len(imp)/2), whole=False)
    # Actual freq from normalized freq
    freqs = w / np.pi * fNyq
    # Magnitude to dB:
    magdB = 20 * np.log10(abs(h))
    return freqs, magdB


def read_pcms(drc_set):
    fnames = []
    for ch in ('L', 'R'):
        fnames.append(f'{LSPK_FOLDER}/drc.{ch}.{drc_set}.pcm')
    IRs = []
    for fname in fnames:
        imp = readPCM32(fname)
        IRs.append( {'fs':      FS,
                     'imp':     imp,
                     'drc_set': fname.split('.')[-2],
                     'channel': fname.split('.')[-3],
                     } )
    return IRs


def diracs():
    IRs = []
    for ch in ('L', 'R'):
        imp = np.zeros(512)
        imp[0] = 1.0
        IRs.append( {'fs':      FS,
                     'imp':     imp,
                     'drc_set': 'none',
                     'channel': ch
                     } )
    return IRs


def get_drc_sets():
    files   = os.listdir(LSPK_FOLDER)
    coeffs  = [ x.replace('.pcm', '') for x in files ]
    drc_coeffs = [ x for x in coeffs if x[:4] == 'drc.'  ]
    #print('drc_coeffs:', drc_coeffs) # debug
    drc_sets = []
    for drc_coeff in drc_coeffs:
        drcSetName = drc_coeff[6:]
        if drcSetName not in drc_sets:
            drc_sets.append( drcSetName )
    return drc_sets + ['none']


if __name__ == '__main__':

    CONFIG = yaml.safe_load( open(f'{UHOME}/pe.audio.sys/config.yml',
                                  'r') )
    FS = float( CONFIG["jack_backend_options"].split('-r')[1]
                                              .split()[0].strip() )
    verbose = True
    if sys.argv[1:]:
        LSPK = sys.argv[1]
        if sys.argv[2:] and '-q' in sys.argv[2]:
            verbose = False
    else:
        print(__doc__)
        exit()

    LSPK_FOLDER = f'{UHOME}/pe.audio.sys/loudspeakers/{LSPK}'
    drc_sets = get_drc_sets()

    plt.style.use('dark_background')
    freq_ticks  = [20, 50, 100, 200, 500, 1e3, 2e3, 5e3, 1e4, 2e4]
    freq_labels = ['20', '50', '100', '200', '500', '1K', '2K', '5K',
                   '10K', '20K']

    for drc_set in drc_sets:

        if verbose:
            print( f'(drc2png) working: {LSPK} - {drc_set} ... .. .' )

        fig, ax = plt.subplots()
        fig.set_figwidth( 10 ) # inches
        fig.set_figheight( 3 )
        fig.set_facecolor( RGBweb )
        ax.set_facecolor( RGBweb )
        ax.set_xscale('log')
        ax.set_xlim( 20, 20000 )
        ax.set_ylim( -15, 5 )
        ax.set_xticks( freq_ticks )
        ax.set_xticklabels( freq_labels )
        ax.set_title( drc_set )

        if drc_set != 'none':
            IRs = read_pcms( drc_set )
        else:
            IRs = diracs()

        for IR in IRs:
            freqs, magdB = get_spectrum( IR["imp"], FS )
            ax.plot(freqs, magdB,
                    label=f'{IR["channel"]}',
                    color={'L': 'cyan', 'R': 'red'}[ IR["channel"] ],
                    linewidth=3
                    )

        ax.legend( facecolor=RGBweb )
        fpng = f'{UHOME}/pe.audio.sys/share/www/images/drc_{drc_set}.png'
        plt.savefig( fpng, facecolor=RGBweb )
        if verbose:
            print( f'(drc2png) saved: \'{fpng}\' ' )
        #plt.show()
