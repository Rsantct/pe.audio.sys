These are sample files.

You could use the **`template.peq`** file for your custom PEQ settings placed in your LOUDSPEAKER folder.

This is a 8-band example. You can use as many **`fil_N:`** 4-band sections as you need.


        # Chainsetup name
        cs-name: flat
        
        #       global:  OnOff,            Gain
        #       pN:      OnOff, Freq, BW,  Gain

        left:
            fil_0:
                global:  1,                 0.0
                p0:      1,     10,   1.0,  0.0
                p1:      1,     10,   1.0,  0.0
                p2:      1,     10,   1.0,  0.0
                p3:      1,     10,   1.0,  0.0
            fil_1:
                global:  1,                 0.0
                p0:      1,     10,   1.0,  0.0
                p1:      1,     10,   1.0,  0.0
                p2:      1,     10,   1.0,  0.0
                p3:      1,     10,   1.0,  0.0

        right:
            fil_0:
                global:  1,                 0.0
                p0:      1,     10,   1.0,  0.0
                p1:      1,     10,   1.0,  0.0
                p2:      1,     10,   1.0,  0.0
                p3:      1,     10,   1.0,  0.0
            fil_1:
                global:  1,                 0.0
                p0:      1,     10,   1.0,  0.0
                p1:      1,     10,   1.0,  0.0
                p2:      1,     10,   1.0,  0.0
                p3:      1,     10,   1.0,  0.0
