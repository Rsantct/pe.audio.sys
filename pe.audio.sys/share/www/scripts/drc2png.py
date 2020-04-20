#!/usr/bin/env python3
""" usage:      drc2png.py [--quiet]
"""

import sys
import os
UHOME = os.path.expanduser("~")
import numpy as np
from scipy import signal
from matplotlib import pyplot as plt
import yaml

webColor = (.15, .15, .15)   # same as index.html background-color: rgb(38, 38, 38);
# https://matplotlib.org/2.0.2/examples/color/named_colors.html
lineRED  = 'indianred'
lineBLUE = 'steelblue'

CONFIG      = yaml.safe_load(open(f'{UHOME}/pe.audio.sys/config.yml','r'))
LSPK        = CONFIG["loudspeaker"]
LSPK_FOLDER = f'{UHOME}/pe.audio.sys/loudspeakers/{LSPK}'


def get_Bfir_sample_rate():
    """ retrieve loudspeaker's filters FS from its Brutefir configuration
    """
    FS = 0
    for fname in (f'{LSPK_FOLDER}/brutefir_config',
                  f'{UHOME}/.brutefir_defaults'):
        with open(fname, 'r') as f:
            lines = f.readlines()
        for l in lines:
            if 'sampling_rate:' in l and l.strip()[0] != '#':
                try:
                    FS = int( [x for x in l.replace(';', '').split()
                                         if x.isdigit() ][0] )
                except:
                    pass
        if FS:
            break   # stops searching if found under lskp folder

    if not FS:
        raise ValueError('unable to find Brutefir sample_rate')

    if 'defaults' in fname:
        print( f'(drc2png) *** using .brutefir_defaults SAMPLE RATE ***' )

    return FS


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

    verbose = True
    if sys.argv[1:]:
        if '-q' in sys.argv[1]:
            verbose = False
        if '-h' in sys.argv[1]:
            print(__doc__)
            exit()

    FS = get_Bfir_sample_rate()
    if verbose:
        print( f'(drc2png) using sample rate: {FS}' )

    drc_sets = get_drc_sets()

    plt.style.use('dark_background')
    plt.rcParams.update({'font.size': 6})
    freq_ticks  = [20, 50, 100, 200, 500, 1e3, 2e3, 5e3, 1e4, 2e4]
    freq_labels = ['20', '50', '100', '200', '500', '1K', '2K',
                   '5K', '10K', '20K']

    for drc_set in drc_sets:

        if verbose:
            print( f'(drc2png) working: {LSPK} - {drc_set} ... .. .' )

        fig, ax = plt.subplots()
        fig.set_figwidth( 5 ) # 5 inches at 100dpi => 500px wide
        fig.set_figheight( 1.5 )
        fig.set_facecolor( webColor )
        ax.set_facecolor( webColor )
        ax.set_xscale('log')
        ax.set_xlim( 20, 20000 )
        ax.set_ylim( -15, 5 )
        ax.set_xticks( freq_ticks )
        ax.set_xticklabels( freq_labels )
        ax.set_title( f'DRC: {drc_set}' )

        if drc_set != 'none':
            IRs = read_pcms( drc_set )
        else:
            IRs = diracs()

        for IR in IRs:
            freqs, magdB = get_spectrum( IR["imp"], FS )
            ax.plot(freqs, magdB,
                    label=f'{IR["channel"]}',
                    color={'L': lineBLUE, 'R': lineRED}
                          [ IR["channel"] ],
                    linewidth=3
                    )

        ax.legend( facecolor=webColor, loc='lower right')
        fpng = f'{UHOME}/pe.audio.sys/share/www/images/drc_{drc_set}.png'
        plt.savefig( fpng, facecolor=webColor )
        if verbose:
            print( f'(drc2png) saved: \'{fpng}\' ' )
        #plt.show()
