#!/usr/bin/env python3
""" BETA EXPERIMENTAL
"""
# CHUNK DIVIDER (figure out by analyzing the raw plotting below)
DIVIDER = b'\x00'

from matplotlib import pyplot as plt
import sys

def b2hex(b):
    """ converts a bytes stream into a easy readable raw hex list, e.g:
        in:     b'\x00-m-i)m\xbb\xff'
        out:    ['00', '2d', '6d', '2d', '69', '29', '6d', 'bb', 'ff']
    """
    bh = b.hex()
    return [ bh[i*2:i*2+2] for i in range(int(len(bh)/2)) ]


log = open( sys.argv[1], 'rb').read()
# split into chunks by the divider
chunks = log.split(DIVIDER)
# restore the divider
chunks = [DIVIDER + x for x in chunks]

# Search for uniques and counting their occurrences
uniques={}
for chunk in chunks:
    if not chunk:
        continue
    if not chunk in uniques:
        uniques[chunk] = 1
    else:
        uniques[chunk] = uniques[chunk] + 1

# Print results
print()
print('times:  sequence:')
for unique in sorted(uniques):
    # times
    print( str(uniques[unique]).rjust(4) + '    ',  end='')
    #            sequence
    print( ' '.join( b2hex(unique) ) )


# Raw plotting
bytes2ints = [x for x in log]
plt.plot(bytes2ints)
plt.title(sys.argv[1])
plt.show()
