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

ZEROS    =   CONFIG["alsamixer"]["zero"]

try:
    if type(ZEROS) == int:
        ZEROS = [ZEROS]
    if type(ZEROS) != list:
        ZEROS = [int(x) for x in ZEROS.split(',')]
except:
    raise Exception('(alsa.py) config.py alsamixer:zero must be a list')

STEP_dB = float(CONFIG["alsamixer"]["step_dB"])

# DEBUG
#print('limits', VMIN, VMAX)
#print('zero', ZEROS)
#print('step_dB', STEP_dB)

####
# The mixer object to deal with
####
m = alsaaudio.Mixer(control=CONTROL, device=DEVICE)


def amixerValue2percent(value):
    """ Mixer.setvolume() manages percents,
        instead of raw 'amixer' values
    """
    percent = int(round((value - VMIN) / (VMAX - VMIN) * 100))
    #print('percent', percent)
    return percent


def dB2amixerValue(dB, zero):
    """ Find the proper value to send to 'amixer',
        as per the zero and step_dB settings
    """
    value = (zero + dB / STEP_dB)
    #print('value', value)
    return value


def dB2percents(dB):
    """ Main routine to adjust the soundcard channels as per de desired dB level
    """

    percents = []
    dBs_pending = []

    for i, zero in enumerate(ZEROS):

        value = dB2amixerValue(dB, zero)

        errors = ''

        if value < VMIN:
            dB_pending = (value - VMIN) * STEP_dB
            dBs_pending.append(dB_pending)
            value = VMIN

        elif value > VMAX:
            dB_pending = (value - VMAX) * STEP_dB
            dBs_pending.append(dB_pending)
            value = VMAX

        else:
            dB_pending = 0
            dBs_pending.append(dB_pending)

        percent = amixerValue2percent(value)
        percents.append(percent)

    return percents, dBs_pending


def set_amixer_gain(dB):
    """ NOTICE: Old versions of Python-alsaaudio doest not manage dB values,
        just percent values over the 'amixer' limit values of a Mixer element.
    """

    error = ''

    # First of all we need to know if any channel clamps (dBs_pending)
    percents, dBs_pending = dB2percents(dB)
    pending = max(dBs_pending)

    # DEBUG
    #print('percents:   ', percents)
    #print('dBs pending:', dBs_pending, pending)

    # If there are different dBs pending along the sound card channels,
    # we must regress and limit the volume applied in alsamixer, since
    # the volume control of the convolver is executed on all the channels
    # at the same time

    if len( set(dBs_pending) ) > 1:
        percents, dBs_pending = dB2percents(dB - pending)
        # DEBUG
        #print('percents:   ', percents)
        #print('dBs pending:', dBs_pending) # Now MUST be all zeros here

    # Finally apply to amixer:
    for i, percent in enumerate(percents):
        try:
            m.setvolume(percent, i) # (percent, channel)
        except Exception as e:
            error = str(e)
            break

    if error:
        print(f'(alsa.py) ERROR: {error}')

    if pending or error:
        result = f'clamped, dB pending: {pending}'
        print(f'(alsa.py) INFO: clamped, dB pending: {pending}')
    else:
        result = 'done'

    return result
