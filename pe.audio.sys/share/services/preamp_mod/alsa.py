#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.
"""
    Manages an alsa mixer element for volume control purposes
"""

import  sys
import  os
import  alsaaudio
from    subprocess import check_output
from    pkg_resources import get_distribution

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from config import  CONFIG


def init_globals():

    def version_ge_v10(vxx):
        """ check if 'vxx' is greater or equal to 0.10.0 """
        v10 = '0.10.0'.split('.')
        vxx = vxx.split('.')
        v10w = 10*int(v10[0]) + 1*int(v10[1])
        vxxw = 10*int(vxx[0]) + 1*int(vxx[1])
        if vxxw >= v10w:
            return True
        else:
            return False


    def get_version():
        try:
            v = get_distribution('pyalsaaudio').version
            return v
        except:
            return '0.0.0'


    def get_zeros(mixer=None, vmin=0, vmax=255):
        """ get configured zero values
        """
        zeros = CONFIG["alsamixer"]["zeros"]

        try:
            if type(zeros) == int:
                zeros = [zeros]
            if type(zeros) != list:
                zeros = [int(x) for x in zeros.split(',')]
        except:
            raise Exception('(alsa.py) config.py alsamixer:zero must be a list')

        if len(zeros) != len( mixer.getvolume() ):
            raise Exception('(alsa.py) config.py alsamixer:zeros list must match control channels')

        if any( [ x for x in zeros if (x<vmin or x>vmax)] ):
            raise Exception('(alsa.py) config.py alsamixer:zeros out of limits')

        return zeros


    def get_step_dB():
        return float(CONFIG["alsamixer"]["step_dB"])


    def get_limits():

        limits  =   CONFIG["alsamixer"]["limits"]

        if type(limits) == str:
            limits = [int(x) for x in limits.split(',')]

        if type(limits) != list or len(limits) != 2:
            raise Exception('(alsa.py) config.py alsamixer:limits must be a LIST')

        (vmin, vmax) = limits

        if vmin < 0 or vmin > 255 or vmax < 0 or vmax > 255 or vmin > vmax:
            raise Exception('(alsa.py) WRONG config.py alsamixer:limits values')

        return (vmin, vmax)


    def get_mixer():
        device = CONFIG["jack"]["device"].split(',')[0]
        try:
            control =   CONFIG["alsamixer"]["control"]
        except:
            control = 'Master'
        mixer = alsaaudio.Mixer(control=control, device=device)
        return mixer


    global MIXER, VMIN, VMAX, ZEROS, STEP_dB, VERSION, VGE10

    VERSION     = get_version()
    VGE10       = version_ge_v10(VERSION)
    MIXER       = get_mixer()
    VMIN, VMAX  = get_limits()
    ZEROS       = get_zeros(MIXER, VMIN, VMAX)
    STEP_dB     = get_step_dB()


def raw2percent(raw):
    percent = int(round((raw - VMIN) / (VMAX - VMIN) * 100))
    return percent


def percent2raw(percent):
    raw = int(round( VMIN + (VMAX - VMIN) * percent / 100 ))
    return raw


def dB2raw(dB, zero):
    """ Calculates the proper raw value to send to 'amixer',
        as per the zero and step_dB settings
    """
    raw = int(round((zero + dB / STEP_dB)))
    return raw


def dB2values(dB, mode='raw'):
    """ Main routine to adjust the soundcard channels
        as per the desired dB level
    """

    values = []
    dBs_pending = []

    for i, zero in enumerate(ZEROS):

        value = dB2raw(dB, zero)

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

        if mode == 'percentage':
            value = raw2percent(value)
        values.append(value)

    return values, dBs_pending


def _set_amixer_gain(dB, mode='percentage'):
    """ This manages VOLUME_UNITS_RAW or VOLUME_UNITS_PERCENTAGE

        RETURNS: 'done' OR 'some_info XX.X'
                 Where XX.X are the dB to be managed by core.py
    """
    error = ''

    # First of all we need to know if any channel clamps (dBs_pending)
    values, dBs_pending = dB2values(dB, mode=mode)
    pending = max(dBs_pending)

    # DEBUG
    #print('values:     ', values)
    #print('dBs pending:', dBs_pending, pending)

    # If there are different dBs pending along the sound card channels,
    # we must regress and limit the volume applied in alsamixer, since
    # the volume control of the convolver is executed on all the audio channels
    # at the same time

    if len( set(dBs_pending) ) > 1:
        values, dBs_pending = dB2values(dB - pending, mode=mode)
        # DEBUG
        #print('NEW values:     ', values)
        #print('NEW dBs pending:', dBs_pending, '<-- MUST be all zeros here')

    # Finally apply to amixer:
    for i, value in enumerate(values):
        try:
            if mode=='raw':
                MIXER.setvolume(value, i, units=alsaaudio.VOLUME_UNITS_RAW)
            else:
                # old versions does not manage 'units' argument, defaults to percentage
                MIXER.setvolume(value, i)
        except Exception as e:
            error = str(e)
            print(f'(alsa.py) ERROR: {error}')
            break

    if error :
        print(f'(alsa.py) ERROR with MIXER, dB pending: {dB}')
        result = f'ALSA ERROR, dB pending: {dB}'

    elif pending :
        print(f'(alsa.py) CLAMPED: dB pending: {pending}')
        result = f'ALSA clamped, dB pending: {pending}'

    else:
        result = 'done'

    return result


def set_amixer_gain(dB):
    """ (i) NOTICE:

        - Old versions of pyalsaaudio only manages VOLUME_UNITS_PERCENTAGE
        - Version 0.10.0 FAILS to manage VOLUME_UNITS_DB, but VOLUME_UNITS_RAW works well.

        We prefer to avoid percentages due to loss of resolution.
    """

    if VGE10:
        return _set_amixer_gain(dB, mode='raw')
    else:
        return _set_amixer_gain(dB, mode='percentage')


init_globals()

print(f'(alsa.py) INFO:')
print(f'    pyalsaaudio:    {VERSION}')
print(f'    vmin:           {VMIN}')
print(f'    vmax:           {VMAX}')
print(f'    zeros:          {ZEROS}')
print(f'    step_dB:        {STEP_dB}')
