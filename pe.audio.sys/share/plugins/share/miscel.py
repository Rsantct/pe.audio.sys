#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    A shared module for plugins.
"""

import  os
from    subprocess  import Popen, DEVNULL

THISDIR      = os.path.dirname( os.path.realpath(__file__) )


def do_3_beep():
    """
       Makes a 3 beep sound at -10 dB

        (i) Needs a 'brutefir' ALSA device, see .asoundrc.sample
    """

    beepPath    = f'{THISDIR}/3beeps_-10dBFS.wav'

    Popen( ['aplay', '-Dbrutefir', beepPath],   stdout=DEVNULL,
                                                stderr=DEVNULL )


