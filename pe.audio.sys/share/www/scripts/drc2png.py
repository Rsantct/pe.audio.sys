#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

""" usage:      drc2png.py [--quiet]

    NOTICE: Even if short lenght IR are used for DRC, thus low resolution
            in low freq correction, the correction curve will be
            oversampled in order to show a smoothed low freq region.
"""

import  numpy as np
from    scipy       import signal
from    matplotlib  import pyplot as plt
import  sys
import  os

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from config import MAINFOLDER, LOUDSPEAKER, LSPK_FOLDER
from miscel import read_bf_config_fs
from brutefir_mod import get_config as bf_get_config

IMGFOLDER   = f'{MAINFOLDER}/share/www/images/{LOUDSPEAKER}'


# ----------------------    Plot config      -----------------------------------
# Same color as index.html background-color: rgb(38, 38, 38)
WEBCOLOR    = (.15, .15, .15)
# https://matplotlib.org/2.0.2/examples/color/named_colors.html
LINERED     = 'indianred'
LINEBLUE    = 'steelblue'
plt.style.use('dark_background')
plt.rcParams.update({'font.size': 6})
FREQ_LIMITS = [20, 20000]
FREQ_TICKS  = [20, 50, 100, 200, 500, 1e3, 2e3, 5e3, 1e4, 2e4]
FREQ_LABELS = ['20', '50', '100', '200', '500', '1K', '2K', '5K', '10K', '20K']
DB_LIMITS   = [-20, +9]
DB_TICKS    = [-18, -12, -6, 0, 6]
DB_LABELS   = ['-18', '-12', '-6', '0', '6']


def get_spectrum(imp, fs):

    fNyq = fs / 2.0

    # Oversampling short taps IRs to display "hires" low freq region.
    # Zeropadding up to Fs / 4 Hz
    Ntaps = int(fs / 4)
    if len(imp) < Ntaps:
        imp= np.pad(imp, (0, Ntaps - len(imp)), 'linear_ramp')
        print('(drc2png) Smoothing low freq curve because low resolution correction impulse')

    # Semispectrum (whole=False -->  w to Nyquist)
    w, h = signal.freqz(imp, worN=int(len(imp) / 2), whole=False)

    # Actual freq from normalized freq
    freqs = w / np.pi * fNyq

    # Magnitude to dB:
    magdB = 20 * np.log10(abs(h))

    return freqs, magdB


def read_pcms(drc_set):

    def readPCM32(fname):
        """ reads impulse from a pcm float32 file
        """
        #return np.fromfile(fname, dtype='float32')
        return np.memmap(fname, dtype='float32', mode='r')


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
    """ find loudspeaker's drc_sets """
    files   = os.listdir(LSPK_FOLDER)
    coeffs  = [ x.replace('.pcm', '') for x in files if x[:4] == 'drc.']
    drc_coeffs = [ x for x in coeffs if x[:4] == 'drc.'  ]
    #print('drc_coeffs:', drc_coeffs) # debug
    drc_sets = []
    for drc_coeff in drc_coeffs:
        drcSetName = drc_coeff[6:]
        if drcSetName not in drc_sets:
            drc_sets.append( drcSetName )
    return drc_sets


def get_coeff_atten(drc_set, ch):

    def get_atten():
        atten = 0.0
        for c in BF_DRC_COEFFS:
            ch_name, set_name = c["name"].split('.')[1:]
            if drc_set ==  set_name and ch == ch_name:
                atten = float(c["atten"])
                break
        return atten


    if drc_set == 'none':
        atten = 0.0
    else:
        atten = get_atten()

    return atten


def png_is_outdated(drc_set):
    """ check datetime of drcXXX.png file versus drcXXX.pcm file """

    if drc_set == 'none':
        png_path = f'{IMGFOLDER}/drc_none.png'
        if os.path.isfile( png_path ):
            return False

    for ch in 'L', 'R':
        # pcm path do exists because pcm_sets is derived from the pcm files
        pcm_path = f'{LSPK_FOLDER}/drc.{ch}.{drc_set}.pcm'
        # png path might not exist
        png_path = f'{IMGFOLDER}/drc_{drc_set}.png'
        try:
            pcm_ctime = os.path.getctime(pcm_path) # the lower one
            png_ctime = os.path.getctime(png_path)
            if (png_ctime - pcm_ctime) < 0:
                if verbose:
                    print(f'(drc2png) found old PNG file for "{drc_set}"')
                return True
        except:
            if verbose:
                print(f'(drc2png) PNG file for "{drc_set}" not found')
            return True

    return False


def prepare_IMGFOLDER():
    try:
        os.mkdir(IMGFOLDER)
    except FileExistsError:
        pass
    except:
        print(f'drc2png unexpected error when mkdir "{IMGFOLDER}"')


if __name__ == '__main__':

    # Reading drc coeffs inside brutefir_config in order to get coeff attenuation
    bf_coeffs = bf_get_config()["coeffs"]
    BF_DRC_COEFFS = [x for x in bf_coeffs if x["name"].startswith('drc')]

    # Read command line (quiet mode or help)
    verbose = True
    if sys.argv[1:]:
        if '-q' in sys.argv[1]:
            verbose = False
        if '-h' in sys.argv[1]:
            print(__doc__)
            exit()

    # Prepare loudspeaker image folder
    prepare_IMGFOLDER()


    # Get sample rate
    FS = read_bf_config_fs()
    if verbose:
        print( f'(drc2png) using sample rate: {FS}' )

    # Get DRC sets names
    drc_sets = get_drc_sets()

    # Do plot png files from pcm files
    drc_sets.append('none')
    for drc_set in drc_sets:

        # Check for outdated PNG file
        if not png_is_outdated(drc_set):
            if verbose:
                print(f'(drc2png) found PNG file for {LOUDSPEAKER}: {drc_set}')
            continue
        else:
            if verbose:
                print(f'(drc2png) processing PNG file for {LOUDSPEAKER}: {drc_set}')

        fig, ax = plt.subplots()
        fig.set_figwidth( 5 )   # 5 inches at 100dpi => 500px wide
        fig.set_figheight( 1.5 )
        fig.set_facecolor( WEBCOLOR )
        ax.set_facecolor( WEBCOLOR )

        ax.set_xscale('log')
        ax.set_xlim( FREQ_LIMITS )
        ax.set_xticks( FREQ_TICKS )
        ax.set_xticklabels( FREQ_LABELS )

        ax.set_ylim( DB_LIMITS )
        ax.set_yticks( DB_TICKS )
        ax.set_yticklabels( DB_LABELS )

        #ax.set_title( f'DRC: {drc_set}' )

        if drc_set != 'none':
            IRs = read_pcms( drc_set )
        else:
            IRs = diracs()

        # Each IR has the following fields: fs, imp, drc_set, channel
        for IR in IRs:
            freqs, magdB = get_spectrum( IR["imp"], FS )
            atten = get_coeff_atten( IR["drc_set"], IR["channel"] )
            magdB -= atten
            ax.plot(freqs, magdB,
                    label=f'{IR["channel"]}',
                    color={'L': LINEBLUE, 'R': LINERED}
                          [ IR["channel"] ],
                    linewidth=3
                    )

        ax.legend( facecolor=WEBCOLOR, loc='lower right')
        fpng = f'{IMGFOLDER}/drc_{drc_set}.png'
        plt.savefig( fpng, facecolor=WEBCOLOR )
        if verbose:
            print( f'(drc2png) saved: \'{fpng}\' ' )
        #plt.show()
