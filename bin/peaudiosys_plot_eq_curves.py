#!/usr/bin/env python3
"""
    Plots the available curves for the Brutefir smooth EQ module,
    by default located under the 'pe.audio.sys/share/eq' folder.

    example of usage:

    peaudiosys_plot_eq_curves.py   bass   [/path/to/folder]

"""
import sys, os
import numpy as np
from matplotlib import pyplot as plt

UHOME       = os.path.expanduser("~")
EQ_FOLDER   = f'{UHOME}/pe.audio.sys/share/eq'


def get_curve_files(fpattern):

    mag_files = [x for x in EQ_FILES if (fpattern in x) and ('mag.dat' in x) ]

    if len(mag_files) == 0:
        raise ValueError(f'not files found for pattern \'{fpattern}\'')
    elif len(mag_files) > 1:
        raise ValueError(f'too much \'{fpattern}\' .dat files')

    mag_file = mag_files[0]
    pha_file = mag_file.replace('_mag', '_pha')

    return mag_file, pha_file


def get_freq_file():

    freq_files = [x for x in EQ_FILES if 'freq.dat' in x ]

    if len(freq_files) > 1:
        raise ValueError('too much freq.dat files')

    return freq_files[0]


if __name__ == '__main__':

    # Read command line
    plot_pha = True
    if not sys.argv[1:]:
        print(__doc__)
        exit()
    else:
        fpattern = sys.argv[1]
        for opc in sys.argv[2:]:
            if '-h' in opc[0:]:
                print(__doc__)
                exit()
            elif opc[0] != '-':
                EQ_FOLDER = opc

    EQ_FILES = os.listdir(EQ_FOLDER)

    # Read the filename for the given pattern
    freq_fname              = get_freq_file()
    mag_fname, pha_fname    = get_curve_files( fpattern )

    # Load data from files
    freq = np.loadtxt( f'{EQ_FOLDER}/{freq_fname}' )
    mags = np.loadtxt( f'{EQ_FOLDER}/{mag_fname}'  )
    try:
        phas = np.loadtxt( f'{EQ_FOLDER}/{pha_fname}'  )
    except:
        print(f'(i) ERROR loading phase from \'{pha_fname}\'')
        plot_pha = False

    # Special case single curve .dat files (target curve)
    if len(mags.shape) == 1:
        mags = mags.reshape(1, mags.shape[0])
        phas = phas.reshape(1, phas.shape[0])

    # Auto transpose if needed
    if len(mags.shape) > 1 and mags.shape[1] != freq.shape[0]:
        print(f'(i) The array of curves have the former Matlab arrangement')
        print(f'    freq: {freq.shape}')
        print(f'    mag:  {mags.shape}')
        mags = mags.transpose()
        phas = phas.transpose()

    # Prepare the plot
    fig, (axMag, axPha) = plt.subplots(2, 1, figsize=(6,6))
    fig.subplots_adjust(hspace=.4)

    axMag.set_title(mag_fname)
    axMag.set_ylabel('dB')
    # A reduced dB span for single curves (e.g: target curves)
    if not any([x in mag_fname for x in ('bass', 'treb', 'loud')]):
        axMag.set_ylim(-12, 12)

    axPha.set_ylabel('deg')
    axPha.set_ylim(-50, 50)
    if plot_pha:
        axPha.set_title(pha_fname)

    # Plot curves
    for curve in mags[:,]:
        axMag.semilogx ( freq, curve )

    if plot_pha:
        for curve in phas:
            axPha.semilogx ( freq, curve )

    plt.show()
