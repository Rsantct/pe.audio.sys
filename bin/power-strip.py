#!/usr/bin/env python3
"""
    A module to manage an USB controlled power outlet, if compatible
    with 'Gembird SIS-PM', as the model 'EnerGenie EG-PMS2'.

    More info:   apt show sispmctl

    Usage:

    power-strip.py                                          show state
    power-strip.py  toggle|on|off  (out# out# ....)|all     changes state
    power-strip.py  --help                                  this help


    NOTICE: The YAML file 'power-strip.yml' associated with this script
            labels the strip's outlets.

"""
import sys
import os
import subprocess as sp
import yaml


OUTLETS = {1:'', 2:'', 3:'', 4:''}
try:
    thispath = os.path.dirname(os.path.abspath(__file__))
    with open(thispath + '/regleta.yml', 'r') as f:
        OUTLETS = yaml.safe_load(f)
except Exception as e:
    print(str(e))


def set_outlet(outlet, mode):
    try:
        mode = { 'on': '-o', 'off': '-f',
                 'toggle': '-t' , 'cambia': '-t' }[mode]
        with open( '/dev/null', 'w') as fnull:
            # "sp.call" is blocking
            sp.call( ( 'sispmctl ' + mode + ' ' + str(outlet) +
                       '>/dev/null 2>&1' ).split(),
                     stdout=fnull, stderr=fnull )
        return True
    except:
        return False


def set_outlets(outlets=[], mode='on'):

    res = []

    for oid in outlets:
        res.append( set_outlet(oid, mode) )

    return res


def get_outlet(outlet):
    try:
        response =  sp.check_output( ('sispmctl -m ' + str(outlet) +
            '>/dev/null 2>&1' ).split() ).decode()
        return response.split()[-1]
    except:
        return None


def get_outlets(outlets=[1,2,3,4], verbose=False):

    state = []

    for o in outlets:
        o_state = get_outlet(o)
        state.append(o_state)
        if verbose:
            print( str(o).ljust(3) + OUTLETS[o].ljust(15) + o_state )

    return state


if __name__ == "__main__":


    targets = []

    if sys.argv[1:]:

        for opc in sys.argv[1:]:
            if opc in ( "toggle" , "on", "off", "cambia"):
                mode = opc
            if opc in ("1", "2", "3", "4" , "all"):
                targets.append(opc)
            if "-h" in opc:
                print(__doc__)
                sys.exit()

    else:
        get_outlets(verbose=True)
        sys.exit()

    if mode and targets:
        for target in targets:
            set_outlet(target, mode)
