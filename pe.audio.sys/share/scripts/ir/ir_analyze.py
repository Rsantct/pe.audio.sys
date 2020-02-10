#!/usr/bin/env python3
""" BETA EXPERIMENTAL
    usage:
        ir_analize.py  rawBytesLogFname [-np]
            -np skips to plot the graph
"""

# CONFIGURE HERE THE CHUNK DIVIDER
# (i) usually 00, but figure out by analyzing the ir.py -t console
#     and the raw plotting below
DIVIDER = b'\x00'

import sys

def b2hex(b):
    """ converts a bytes stream into an easy readable raw hex list, e.g:
        in:     b'\x00-m-i)m\xbb\xff'
        out:    ['00', '2d', '6d', '2d', '69', '29', '6d', 'bb', 'ff']
    """
    bh = b.hex()
    return [ bh[i*2:i*2+2] for i in range(int(len(bh)/2)) ]


if not sys.argv[1:]:
    print(__doc__)
    exit()
else:
    flogname = sys.argv[1]

# read the rawBytesLogFname
log = open( flogname, 'rb').read()
# split into chunks by the divider
chunks = log.split(DIVIDER)
# restore the divider
chunks = [DIVIDER + x for x in chunks]

# search for uniques and counting occurrences
uniques={}
for chunk in chunks:
    if not chunk:
        continue
    if not chunk in uniques:
        uniques[chunk] = 1
    else:
        uniques[chunk] = uniques[chunk] + 1

# print results
print()
print(f'---- {flogname} ----')
print('times:  sequence:')
for unique in sorted(uniques):
    # times
    print( str(uniques[unique]).rjust(4) + '    ',  end='')
    #            sequence
    print( ' '.join( b2hex(unique) ) )

if "-np" in sys.argv[1:]:
    exit()

# raw plotting
from matplotlib import pyplot as plt
bytes2ints = [x for x in log]
plt.plot(bytes2ints)
plt.title(flogname)
plt.show()
