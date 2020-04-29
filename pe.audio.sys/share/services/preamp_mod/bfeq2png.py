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
"""
    A module to dump an EQ stage graph to share/www/images/brutefir_eq.png

    Command line usage: bfeq2png.py [--verbose]
"""
import sys
import os
from socket import socket
import numpy as np
import matplotlib
# (i) Agg is a SAFE backend to avoid "tkinter.TclError: couldn't connect to display"
#     under certain circumstances.
#     https://matplotlib.org/faq/usage_faq.html#what-is-a-backend
#     Comment out this line if you want to test plotting under your standard backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt


UHOME       = os.path.expanduser("~")
RGBweb      = (.15, .15, .15)   # same as index.html background-color: rgb(38, 38, 38);
lineColor   = 'grey'
verbose     = False

# Prepare pyplot
plt.style.use('dark_background')
plt.rcParams.update({'font.size': 6})
freq_ticks  = [ 20,   50,   100,   200,   500,   1e3,  2e3,  5e3,  1e4,   2e4]
freq_labels = ['20', '50', '100', '200', '500', '1K', '2K', '5K', '10K', '20K']
figHeight   = 1.5   # min 1.5 if font.size = 6

def get_bf_eq():
    """ Queries Brutefir TCP service to get the current EQ magnitudes
    """
    cmd  = 'lmc eq "c.eq" info;'
    ans = ''
    with socket() as s:
        try:
            s.connect( ('localhost', 3000) )
            s.send( f'{cmd}; quit;\n'.encode() )
            while True:
                tmp = s.recv(1024).decode()
                if not tmp:
                    break
                ans += tmp
            s.close()
        except:
            print( f'(bfeq2png) unable to connect to Brutefir:3000' )

    for line in ans.split('\n'):
        if line.strip()[:5] == 'band:':
            freqs = line.split()[1:]
        if line.strip()[:4] == 'mag:':
            mags = line.split()[1:]

    return np.array(freqs).astype(np.float), \
           np.array(mags).astype(np.float)


def do_graph(freqs, magdB):
    """ Dupms a graph to share/www/images/brutefir_eq.png
    """
    if verbose:
        print( f'(bfeq2png) working ... .. .' )

    # Customize figure and axes
    fig, ax = plt.subplots()
    fig.set_figwidth( 5 )   # 5 inches at 100dpi => 500px wide (same as DRC graph)
    fig.set_figheight( figHeight )
    fig.set_facecolor( RGBweb )
    ax.set_facecolor( RGBweb )
    ax.set_xscale('log')
    ax.set_xlim( 20, 20000 )
    ax.set_ylim( -6, +12 )
    ax.set_xticks( freq_ticks )
    ax.set_xticklabels( freq_labels )
    # ax.set_title( 'Brutefir EQ' )
    # Plot the EQ curve
    ax.plot(freqs, magdB,
            color=lineColor,
            linewidth=3
            )
    # Save to file
    fpng = f'{UHOME}/pe.audio.sys/share/www/images/brutefir_eq.png'
    plt.savefig( fpng, facecolor=RGBweb )
    if verbose:
        print( f'(bfeq2png) saved: \'{fpng}\' ' )
    #plt.show()  # (!) PLEASE comment out the safe backend Agg before using this


if __name__ == '__main__':

    if sys.argv[1:]:
        if '-v' in sys.argv[1]:
            verbose = True
        if '-h' in sys.argv[1]:
            print(__doc__)
            exit()

    freqs, magdB = get_bf_eq()
    do_graph(freqs, magdB)
