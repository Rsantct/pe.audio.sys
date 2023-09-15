#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.
"""
    Manages an alsa mixer element for volume control purposes
"""

import sys
import os
import alsaaudio

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from config import  CONFIG

DEVICE = CONFIG["alsamixer"]["device"].split(',')[0]

try:
    CONTROL =   CONFIG["alsamixer"]["control"]
except:
    CONTROL = 'Master'

######
# (i) limits, zero and steps_dB are mandatory for ALSA mixer to work properly
######

limits  =   CONFIG["alsamixer"]["limits"]
if type(limits) == str:
    limits = [int(x) for x in limits.split(',')]
if type(limits) != list or len(limits) != 2:
    raise Exception('(alsa.py) config.py alsamixer:limits must be a LIST')
VMIN, VMAX = limits
if VMIN < 0 or VMAX > 255:
    raise Exception('(alsa.py) WRONG config.py alsamixer:limits values')

ZERO    =   CONFIG["alsamixer"]["zero"]
if type(ZERO) != int:
    raise Exception('(alsa.py) config.py alsamixer:zero must be integer')

STEP_dB = float(CONFIG["alsamixer"]["step_dB"])

# DEBUG
#print('limits', VMIN, VMAX)
#print('zero', ZERO)
#print('step_dB', STEP_dB)

####
# The mixer object to deal with
####
m = alsaaudio.Mixer(control=CONTROL, device=DEVICE)


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


def set_amixer_gain(dB):
    """ OLD versions of Python-alsaaudio doest not manage dB values,
        just percent values over the 'amixer' limit values of a Mixer element.
    """

    # Find the proper value to send to 'amixer',
    # as per the zero and step_dB settings
    value = (ZERO + dB / STEP_dB)
    #print('value', value)

    clamped_info = ''
    if value < VMIN or value > VMAX:
        value = clamp(value, VMIN, VMAX)
        clamped_info = f"amixer '{CONTROL}' was clamped to {value}"

    # Mixer.setvolume() manages percents, instead of raw 'amixer' values
    percent = int(round(value / (VMAX - VMIN) * 100))
    #print('percent', percent)

    try:
        m.setvolume(percent)
        if not clamped_info:
            result = 'done'
        else:
            result = clamped_info
    except Exception as e:
        error = f'(alsa.py) ERROR {str(e)} | Maybe wrong config.py alsamixer settings?'
        print(error)
        result = error

    return result
