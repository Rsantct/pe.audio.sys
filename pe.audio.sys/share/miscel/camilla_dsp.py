#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

import os
import sys
import subprocess as sp
from   time import sleep
from   camilladsp import CamillaClient

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

from   miscel   import process_is_running, LOG_FOLDER, Fmt
import jack_mod as jack


HOST        = '127.0.0.1'
PORT        = 1234

# Compressor config file path
COMPRESSOR_YML = f'{UHOME}/pe.audio.sys/config/camilladsp_compressor.yml'

# The CamillaDSP connection
PC = CamillaClient(HOST, PORT)


def _remove_jack_camilla_from_system_card():

    tries = 10
    while tries:
        x = jack.get_ports('cpal_client', is_audio=True)
        if len(x) == 4:
            break
        tries -= 1
        sleep(.1)

    sleep(.1)   # safest

    if not tries:
        raise Exception('Unable to get CamillaDSP ports in JACK, check log folder.')

    for (is_input, is_output) in ((True, False), (False, True)):

        for cpal_port in jack.get_ports('cpal_client', is_input=is_input, is_output=is_output):

            wired_ports = jack.get_all_connections(cpal_port)

            for p in wired_ports:
                if is_input:
                    jack.connect(p, cpal_port, 'disconnect')
                else:
                    jack.connect(cpal_port, p, 'disconnect')


def _insert_cdsp():

    # disconnect pre_in_loop --> brutefir
    jack.connect('pre_in_loop:output_1', 'brutefir:in.L', 'disconnect')
    jack.connect('pre_in_loop:output_2', 'brutefir:in.R', 'disconnect')


    # connect pre_in_loop --> cpal
    jack.connect('pre_in_loop:output_1', 'cpal_client_in:in_0')
    jack.connect('pre_in_loop:output_2', 'cpal_client_in:in_1')

    # connect cpal --> brutefir
    jack.connect('cpal_client_out:out_0', 'brutefir:in.L')
    jack.connect('cpal_client_out:out_1', 'brutefir:in.R')


def _init():

    def stop_cdsp():

        sp.call('killall -KILL camilladsp 1>/dev/null 2>&1', shell=True)
        sleep(.1) # safest

        tries = 10
        while tries:
            if not process_is_running('camilladsp'):
                break
            tries -= 1
            sleep(.1)
        if not tries:
            raise Exception('Unable to stop CamillaDSP.')


    def run_cdsp(config_file):

        # Starting CamillaDSP **MUTED**
        RATE     = jack.get_samplerate()
        cdsp_cmd = f'camilladsp --wait --mute -r {RATE} -a {HOST} -p {PORT} ' + \
                   f'--logfile "{LOG_FOLDER}/camilladsp.log" {config_file}'

        print(f'{Fmt.MAGENTA}Pleae wait for CamillaDSP to start ...{Fmt.END}')
        p = sp.Popen( cdsp_cmd, shell=True )

        tries = 120
        while tries:
            try:
                PC.connect()
                break
            except:
                tries -= 1
                sleep(.5)

        if not tries:
            raise Exception('Unable to run CamillaDSP, check log folder.')

        print(f'{Fmt.BLUE}Logging CamillaDSP to log/camilladsp.log ...{Fmt.END}')

        # Remove JACK system connections
        _remove_jack_camilla_from_system_card()

        # Inserting before Brutefir
        _insert_cdsp()

        # Unmute
        PC.mute.set_main(False)


    if process_is_running('camilladsp'):
        stop_cdsp()

    run_cdsp(COMPRESSOR_YML)


def mute(mode='state'):

    if mode in (True, 'true', 'on', 1):
        PC.mute.set_main(True)

    if mode in (False, 'false', 'off', 0):
        PC.mute.set_main(False)

    if mode == 'toggle':
        new_mode = {True: False, False: True} [PC.mute.main() ]
        PC.mute.set_main(new_mode)

    return PC.mute.main()


def bypass(step='', mode='state'):

    cfg_active = PC.config.active()
    cfg_new    = cfg_active.copy()

    if 'compressor' in step:

        for i, s in enumerate( cfg_active["pipeline"] ):

            if 'compressor' in s["name"]:

                if mode in (True, 'true', 1, 'on'):
                    cfg_new["pipeline"][i]["bypassed"] = True

                elif mode in (False, 'false', 0, 'off'):
                    cfg_new["pipeline"][i]["bypassed"] = False

                PC.config.set_active(cfg_new)

                return PC.config.active()["pipeline"][i]["bypassed"]


def compressor(mode=''):

    if mode in (True, 'true', 1, 'on'):
        bypass('compressor', False)

    elif mode in (False, 'false', 0, 'off'):
        bypass('compressor', True)

    return  not bypass('compressor', 'state')

