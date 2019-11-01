#!/usr/bin/env python3
"""
    Plots the curves inside a .dat file of those used in
    the Brutefir EQ stage of FIRtro / pre.di.c / pe.audio.sys

    usage:
    
    peaudiosys_plot_eq_curves.py <pattern> [/path/to/folder] [-pha]
    
        -pha    adds the phase plot
    
"""

import sys, os
import numpy as np
from matplotlib import pyplot as plt

def get_curves(fpattern):

    try:
        freq_files = [x for x in EQ_FILES if 'freq.dat' in x ]
        if len(freq_files) > 1:
            raise
        else:
            freq_file = freq_files[0]
    except:
        print( f'\n(!) Problems reading a unique \'xxxfreq.dat\' '
               f'at \'{EQ_FOLDER}\'' )
        exit()

    try:
        mag_files = [x for x in EQ_FILES if f'{fpattern}_mag.dat' in x ]
        if len(mag_files) > 1:
            raise
        else:
            mag_file = mag_files[0]
    except:
        print( f'\n(!) problems reading a unique \'***{fpattern}_mag.dat\' '
               f'at \'{EQ_FOLDER}\'' )
        exit()

    return freq_file, mag_file


if __name__ == '__main__':

    HOME = os.path.expanduser("~")
    EQ_FOLDER = f'{HOME}/pe.audio.sys/share/eq'
    EQ_FILES = os.listdir(EQ_FOLDER)

    # Try to read the optionals /path/to/eq_files_folder
    #                           -pha
    pha = False
    if sys.argv[2:]:
        for opc in sys.argv[2:]:
            if '-pha' in opc:
                pha = True
            elif '-h' in opc[0:]:
                print(__doc__)
                exit()
            else:
                EQ_FOLDER = opc
                EQ_FILES = os.listdir(EQ_FOLDER)

    # Read the filename pattern (mandatory)
    try:
        freq_fname, mag_fname = get_curves( sys.argv[1] )
        pha_fname = mag_fname.replace('_mag','_pha')
    except:
        print(__doc__)
        exit()

    # A .dat file can have one o more curves inside.
    freq = np.loadtxt( f'{EQ_FOLDER}/{freq_fname}' )
    mags = np.loadtxt( f'{EQ_FOLDER}/{mag_fname}' )
    phas = np.loadtxt( f'{EQ_FOLDER}/{pha_fname}' )

    if 'target' in mag_fname:
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
        

    # A single target curve kind of
    if len( mags.shape ) == 1:
        ax1.semilogx ( freq, mags )
        ax1.set_ylim(-6,12)
        if pha:
            ax2.semilogx ( freq, phas )

    # Multiple curves tone or loudness kind of.
    # Looping over the curves inside the .dat file
    else:
        for idx in range( mags.shape[1] ):
            ax1.semilogx ( freq, mags[:,idx], label=idx)
        if not pha:
            ax1.legend( loc="center", bbox_to_anchor=(1.15, 1.05) )
            handles, labels = ax1.get_legend_handles_labels()
            ax1.legend(handles[::-1], labels[::-1])
        if pha:
            for idx in range( phas.shape[1] ):
                ax2.semilogx ( freq, phas[:,idx], label=idx)

    ax1.set_title( mag_fname )
    if pha:
        ax2.set_title( pha_fname )

    plt.show()


