#!/usr/bin/env python3
""" BETA EXPERIMENTAL
"""

from matplotlib import pyplot as plt
import sys

# CHUNK DIVIDER (figure out by analyzing the raw plotting below)
DIVIDER = b'\x00'

log = open( sys.argv[1], 'rb').read()
# split into chunks by values zero
chunks = log.split(DIVIDER)
# restore the zeros
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
print('times:   sequence:')
for unique in sorted(uniques):
    print( str(uniques[unique]).rjust(4) + '    ',  end='')
    for b in unique:
        print(str(b).rjust(4), end='')
    print()

print()
print('         (as bytes)')
for unique in sorted(uniques):
    print( str(uniques[unique]).rjust(4) + '    ',  end='')
    print(unique)

# Raw plotting
bytes2ints = [x for x in log]
plt.plot(bytes2ints)
plt.title(sys.argv[1])
plt.show()
