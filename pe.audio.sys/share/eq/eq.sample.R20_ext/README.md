
Original file names were:

      R20_ext-freq.dat

      R20_ext-bass_mag.dat
      R20_ext-bass_pha.dat
      R20_ext-treble_mag.dat
      R20_ext-treble_pha.dat

      R20_ext-loudness_mag.dat
      R20_ext-loudness_pha.dat

      R20_ext_+6.0-3.0_target_mag.dat
      R20_ext_+6.0-3.0_target_pha.dat


The new file names has been adapted to fit the new (and simple) naming criteria.

Also for multicurve files (bass, treble, loudness):

- the former Matlab arrangement has been transposed to a Numpy one, e.g. rows are now curves and columns corresponds to freq bands as the ones inside `freq.dat`

- data has been flipud: now row indices are directly related to the amount of eq to be applied.


And last, for loudness contour compensation curves:

- the former .dat file had 20 curves, the flat one is at index 13 (well at 7 before flipud). 

- the new .dat file has been front zero padded so that the flat curve index is 83, as per the supposed REFERENCE LISTENING 83 dBSPL.

