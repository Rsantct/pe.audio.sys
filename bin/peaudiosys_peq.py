#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

"""
    Command line tool for the pe.audio.sys Ecasound PEQ plugin.

    Usage:             peq_control.py  cmd  arg1  arg2 ....

    Available commands and arguments:

    - PEQ_dump2peq                  Prints running parametric filters,
                                    also dumps them to LSPK_FOLDER/eca_dump.peq

    - PEQ_dump2ecs                  Prints running .ecs structure
                                    also dumps it to LSPK_FOLDER/eca_dump.ecs

    - PEQ_load_peq  file            Loads a .peq file of parameters in Ecasound

    - PEQ_bypass  on|off|toggle     Bypass the EQ

    - PEQ_gain  XX                  Sets EQ gain

    - ECA_cmd  cmd1 ... cmdN        Native ecasound-iam commands.
                                    (See man ecasound-iam)


    NOTE: .peq files are HUMAN READABLE PEQ settings,
          .ecs files are standard Ecasound chainsetup files.

"""

import  sys
import  os

UHOME       = os.path.expanduser("~")
MAINFOLDER  = f'{UHOME}/pe.audio.sys'
sys.path.append(f'{MAINFOLDER}/share/miscel')

import  peq_control as pc

if __name__ == '__main__':

    # is ecasound listening?
    if not pc.ecanet(''):
        print("(!) no answer from Ecasound server")
        sys.exit()

    # we can pass more than one command from command line to ecasound
    if sys.argv[1:]:

        cmd  = sys.argv[1]
        args = sys.argv[2:]

        if   cmd == "ECA_cmd":
            for ecaCmd in args:
                print( pc.ecanet(ecaCmd) )

        elif cmd == "PEQ_dump2peq":
            pc.eca_dump2peq(verbose=True)

        elif cmd == "PEQ_dump2ecs":
            pc.eca_dump2ecs(verbose=True)

        elif cmd == "PEQ_load_peq" and args:
            pc.eca_load_peq(args[0])

        elif cmd == "PEQ_bypass" and args:
            pc.eca_bypass(args[0])

        elif cmd == "PEQ_gain" and args:
            pc.eca_gain(args[0])

        else:
            print(f'(!) Bad command')
            print(__doc__)

    else:
        print(__doc__)
