#!/usr/bin/env python3
"""
    Plots the curves inside a .dat file of those used in
    the Brutefir EQ stage of FIRtro/pre.di.c/pe.audio.sys

    usage:
        brutefir_view_eq_curvespy  <pattern>  [/path/to/folder]
    
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

    # Try to read the optional /path/to/eq_files_folder
    try:
        EQ_FOLDER = sys.argv[2]
    except:
        pass

    # Read the filename pattern (mandatory)
    try:
        freq_fname, mag_fname = get_curves(sys.argv[1])
    except:
        print(__doc__)
        exit()

    # A .dat file can have one o more curves inside.
    mags = np.loadtxt( f'{EQ_FOLDER}/{mag_fname}' )
    freq = np.loadtxt( f'{EQ_FOLDER}/{freq_fname}' )

    # Prepare the plot
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    # Looping over the curves inside the .dat file
    for idx in range( mags.shape[1] ):
        ax.semilogx ( freq, mags[:,idx], label=idx)

    ax.legend( loc="center", bbox_to_anchor=(1.15, 1.05) )
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1])

    ax.set_title( mag_fname )

    plt.show()


