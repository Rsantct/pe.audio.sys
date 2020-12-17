#!/usr/bin/env python3
"""
    Plots the available curves for the Brutefir smooth EQ module,
    by default located under the 'pe.audio.sys/share/eq' folder.

    usage:

    peaudiosys_plot_eq_curves.py <pattern> [/path/to/folder] [-pha]

        -pha    adds the phase plot

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
    pha = False
    if not sys.argv[1:]:
        print(__doc__)
        exit()
    else:
        fpattern = sys.argv[1]
        for opc in sys.argv[2:]:
            if '-pha' in opc:
                pha = True
            elif '-h' in opc[0:]:
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
    phas = np.loadtxt( f'{EQ_FOLDER}/{pha_fname}'  )

    # Auto transpose if needed
    if mags.shape[1] != freq.shape[0]:
        print(f'(i) array of curves have the former Matlab arrangement')
        print(f'    freq: {freq.shape}')
        print(f'    mag:  {mags.shape}')
        mags = mags.transpose()
        phas = phas.transpose()

    # Prepare the plot
    fig = plt.figure()
    if not pha:
        ax1 = fig.add_subplot(1, 1, 1)
    else:
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)
        fig.subplots_adjust(hspace=.4)

    # Plot curves
    for curve in mags:
        ax1.semilogx ( freq, curve )

    if pha:
        for curve in phas:
            ax2.semilogx ( freq, curve )

    plt.show()
