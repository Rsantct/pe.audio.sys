#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.

# https://henquist.github.io/pycamilladsp/

import os
import sys
import subprocess as sp
import yaml
from   time import sleep
from   camilladsp import CamillaClient

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys/share/miscel')

import jack_mod as jack
from   miscel   import  process_is_running, CONFIG, MAINFOLDER, LOG_FOLDER, Fmt

COMPRESSOR_CYCLE = ['off', '1.0:1', '2.0:1', '3.0:1']

HOST        = '127.0.0.1'
PORT        = 1234

CONFIG_DIR          = f'{MAINFOLDER}/config'
BASE_YML_PATH       = f'{CONFIG_DIR}/camilladsp_base.yml'
RUNTIME_YML_PATH    = f'{CONFIG_DIR}/.camilladsp.yml'

# The CamillaDSP connection
PC = CamillaClient(HOST, PORT)


def _stop_cdsp():

    sp.call('killall -KILL camilladsp 1>/dev/null 2>&1', shell=True)
    sleep(.1) # safest

    tries = 10
    while tries:
        if not process_is_running('camilladsp', 'yml'):
            break
        tries -= 1
        sleep(.1)
    if not tries:
        raise Exception('Unable to stop CamillaDSP.')

    return True


def _connect_to_camilla():

    tries = 15   # 3 sec

    while tries:
        try:
            PC.connect()
            break
        except:
            sleep(.2)
            tries -= 1

    if not tries:
        print(f'{Fmt.RED}Unable to connect to CamillaDSP, check log folder.{Fmt.END}')
        return False

    return True


def _camilla_ports_available():
    """ just checks if all I/O cpal ports are available in jack
    """

    tries = 10

    while tries:

        cpal_in_ports  = jack.get_ports('cpal_client', is_audio=True, is_input=True)
        cpal_out_ports = jack.get_ports('cpal_client', is_audio=True, is_output=True)

        if len( cpal_in_ports ) == 2 and len( cpal_out_ports ) == 2:
            sleep(.25) # safe
            return True

        sleep(.2)
        tries -= 1

    print(f'{Fmt.BOLD}Unable to detect cpal I/O jack ports.{Fmt.END}')

    return False


def _cpal_ports_ok():
    """ Check that no cpal ports are connected to system ports
        AND
        there are no weird cpal ports named like `cpal_client_in-01`
    """

    cpal_ports = jack.get_ports('cpal_client')

    for cpal_port in cpal_ports:

        # Early return if any `cpal_client_in-01` is detected
        if '-' in cpal_port.name:
            print(f'{Fmt.BOLD}Weird CamillaDSP behavior having port: {cpal_port.name}{Fmt.END}')
            return False

        conns = jack.get_all_connections( cpal_port )

        for c in conns:
            if 'system' in c.name:
                print(f'{Fmt.BOLD}CPAL <--> SYSTEM detected: {cpal_port.name} {c.name}{Fmt.END}')
                return False

    return True


def _remove_jack_camilla_from_system_card():
    """ CPAL jack ports will auto connect to
        system:capture and system:playback

        Return True if disconnection is success, else False
    """

    if not _camilla_ports_available():
        return False

    # Disconnecting the auto connected ones
    for (is_input, is_output) in ((True, False), (False, True)):

        for cpal_port in jack.get_ports('cpal_client', is_input=is_input, is_output=is_output):

            wired_ports = jack.get_all_connections(cpal_port)

            for p in wired_ports:

                if not 'system' in p.name:
                    continue

                if is_input:
                    jack.connect(p, cpal_port, 'disconnect')
                else:
                    jack.connect(cpal_port, p, 'disconnect')

    # Double check if any 'system' remains in cpal ports connections
    if _cpal_ports_ok():
        return True
    else:
        return False


def _insert_cdsp():

    # disconnect pre_in_loop --> brutefir (if so)
    for pre_out in ('pre_in_loop:output_1', 'pre_in_loop:output_2'):
        pre_out_clients = jack.get_all_connections(pre_out)
        pre_out_clients = [x.name for x in pre_out_clients]
        for pre_out_client in [c for c in pre_out_clients if 'brutefir' in c.lower()]:
            jack.connect(pre_out, pre_out_client, 'disconnect')

    # connect pre_in_loop --> cpal
    jack.connect('pre_in_loop:output_1', 'cpal_client_in:in_0')
    jack.connect('pre_in_loop:output_2', 'cpal_client_in:in_1')

    # connect cpal --> brutefir
    jack.connect('cpal_client_out:out_0', 'brutefir:in.L')
    jack.connect('cpal_client_out:out_1', 'brutefir:in.R')

    return True


def _init(compressor='off', mode='start'):
    """ defaults to bypass the compressor stage
    """

    def combine_lspk_config():
        """ This merges the BASE YML and the LOUDSPEAKER YML

            returns True if the loudspeaker uses CamillaDSP
        """

        def get_lspk_config():
            """ retunrs void {} if not found a loudspeaker's CamillaDSP yml file
            """

            lspk = CONFIG["loudspeaker"]

            lspk_camilla_yml_path = f'{MAINFOLDER}/loudspeakers/{lspk}/camilladsp_lspk.yml'

            try:
                with open(lspk_camilla_yml_path, 'r') as f:
                    cfg = yaml.safe_load( f.read() )
                print(f'{Fmt.BLUE}Loudspeaker {lspk}/camilladsp.yml was found{Fmt.END}')
                return cfg

            except:
                print(f'{Fmt.BLUE}Loudspeaker {lspk}/camilladsp.yml was NOT found{Fmt.END}')
                return {}


        lspk_uses_cdsp = False

        # Loading the base config
        with open(BASE_YML_PATH, 'r') as f:
            base_config = yaml.safe_load( f.read() )

        # Prepare the runtime config
        runtime_config = base_config

        # Getting and merging the loudspeaker config
        lspk_config = get_lspk_config()

        # merging filters
        if 'filters' in lspk_config:

            lspk_uses_cdsp = True

            runtime_config["filters"] = lspk_config["filters"]

            pipeline_step_names = []

            for f in lspk_config["filters"]:
                pipeline_step_names.append(f)
                print(f'{Fmt.BLUE}Adding filter `{f}` for `{CONFIG["loudspeaker"]}` to CamillaDSP pipeline{Fmt.END}')

            pipeline_step = {
                'type':         'Filter',
                'description':  CONFIG["loudspeaker"],
                'channels':     [0, 1],
                'bypassed':     False,
                'names':        pipeline_step_names
            }

            runtime_config["pipeline"].append( pipeline_step )

        # Setting the safe gain if required:
        safe_gain = 0
        if 'safe_gain' in lspk_config and lspk_config["safe_gain"]:
            safe_gain = lspk_config["safe_gain"]

        # Write runtime configuration in the final YAML file for CamillaDSP to start
        with open(RUNTIME_YML_PATH, 'w') as f:
            yaml.dump(runtime_config, f, default_flow_style=False)

        return lspk_uses_cdsp, safe_gain


    def run_cdsp():

        # Combines base config and loudspeaker config if any
        lspk_uses_camilladsp, global_volume = combine_lspk_config()

        # Early return if not wanted to load CamillaDSP
        if not( lspk_uses_camilladsp or CONFIG["use_compressor"]):
            return False

        # Starting CamillaDSP **MUTED**
        RATE     = jack.get_samplerate()
        cdsp_cmd = f'camilladsp --wait --mute -r {RATE} -a {HOST} -p {PORT} ' + \
                   f'--logfile "{LOG_FOLDER}/camilladsp.log" {RUNTIME_YML_PATH}'

        print(f'{Fmt.MAGENTA}Pleae wait for CamillaDSP to start ...{Fmt.END}')
        p = sp.Popen( cdsp_cmd, shell=True )

        if not _connect_to_camilla():
            return False

        if not _camilla_ports_available():
            return False


        # Loudspeaker's safe_gain --> Main fader volume
        volume(global_volume)

        # Some info
        chunk_size = config()["devices"]["chunksize"]
        fs         = config()["devices"]["samplerate"]
        latency    = int( round(chunk_size / fs * 1e3) )

        print(f'{Fmt.BLUE}CamillaDSP running at {fs} Hz with chunk_size {chunk_size} ({latency} ms){Fmt.END}')
        print(f'{Fmt.BLUE}Logging CamillaDSP to log/camilladsp.log ...{Fmt.END}')

        # Remove JACK system connections
        if not _remove_jack_camilla_from_system_card():
            print(f'{Fmt.BOLD}Cannot disconnect CamillaDSP cpal jack ports from system{Fmt.END}')
            return False

        # Inserting before Brutefir
        if _insert_cdsp():
            print(f'{Fmt.BLUE}CamillaDSP has been inserted in jack.{Fmt.END}')
        else:
            return False

        # Double check
        if not _cpal_ports_ok():
            print(f'{Fmt.BOLD}CamillaDSP remains muted, because bad jack ports.{Fmt.END}')
            return False

        # Unmute
        PC.volume.set_main_mute(False)

        return True


    if process_is_running('camilladsp'):
        _stop_cdsp()

    if mode == 'stop':
        return True

    if not run_cdsp():
        return False


    # Set the compressor (default is bypassed)
    if CONFIG["use_compressor"]:
        _bypass('compressor', not compressor != 'off')

    return True


def _bypass(step_pattern='', mode='state', quiet=True):
    """
        Bypass a pipeline step as per its
        `name` field or `names` list field

        returns: the bypassed state (boolean)
                 OR
                 None if not found
    """

    def get_step_pipeline_index(cfg, step_pattern):

        index = -1

        for i, s in enumerate( cfg["pipeline"] ):

            if 'name' in s and step_pattern in s["name"]:
                index = i

            # Pipeline steps of type `Filter` has `names` instead of `name`
            if 'names' in s:
                for name in s["names"]:
                    if step_pattern in name:
                        index = i
        return index


    cfg = PC.config.active()

    i = get_step_pipeline_index(cfg, step_pattern)

    # Early return if pattern not found
    if i <= 0:
        return None

    if mode in (True, 'true', 1, 'on'):
        cfg["pipeline"][i]["bypassed"] = True

    elif mode in (False, 'false', 0, 'off'):
        cfg["pipeline"][i]["bypassed"] = False

    elif mode == 'toggle':
        cfg["pipeline"][i]["bypassed"] = not cfg["pipeline"][i]["bypassed"]

    # Return the current bypass status
    else:
        return cfg["pipeline"][i]["bypassed"]

    # mute / unmute to avoid pops
    # (i) always sleep(.1) after the `set_active` command
    if quiet:
        mute(True)
        PC.config.set_active(cfg)
        sleep(.1)
        mute(False)

    else:
        PC.config.set_active(cfg)
        sleep(.1)

    return PC.config.active()["pipeline"][i]["bypassed"]


def volume(dB=None, mode='abs'):
    """ get or set the Main fader volume

        mode: 'add' or 'rel' to make relative changes
    """
    try:

        if 'rel' in mode or 'add' in mode:
            dB = PC.volume.volume(0) + dB

        if dB <= 0:
            PC.volume.set_volume(0, dB)

    except Exception as e:
        pass

    return PC.volume.volume(0)


def mute(mode='state'):
    """ Mute camillaDSP

        returns: the mute state (boolean)
    """

    if mode in (True, 'true', 'on', 1):
        PC.volume.set_main_mute(True)

    if mode in (False, 'false', 'off', 0):
        PC.volume.set_main_mute(False)

    if mode == 'toggle':
        new_mode = {True: False, False: True} [PC.volume.main_mute() ]
        PC.volume.set_main_mute(new_mode)


    return PC.volume.main_mute()


def state():
    return PC.general.state().name


def config():
    return PC.config.active()


def compressor(oper='', ratio=''):
    """ Modifies both:
            - the compressor pipeline bypass
            - the compressor processor parameters

        Returns a json string with the compressor state and parameters, example:

            '{"active": True, "threshold": -60.0, "ratio": "3.0:1", "makeup_gain": 26.7}'
    """

    def get_parameters():

        cfg = PC.config.active()
        pms = cfg["processors"]["tv_compressor"]["parameters"]
        threshold   = pms["threshold"]
        factor      = pms["factor"]
        makeup_gain = pms["makeup_gain"]

        return {'threshold':threshold, 'ratio': f'{factor}:1', 'makeup_gain': makeup_gain}


    def rotate_compressor():

        if not _bypass('compressor'):
            current = get_parameters()["ratio"]
        else:
            current = 'off'

        # If current ratio is not included in COMPRESSOR_CYCLE
        try:
            cur_index   = COMPRESSOR_CYCLE.index(current)
        except:
            cur_index = -1

        next_index  = (cur_index + 1) % len(COMPRESSOR_CYCLE)

        new = COMPRESSOR_CYCLE[next_index]

        if new == 'off':
            _bypass('compressor', True)

        else:
            _bypass('compressor', False)
            set_compressor(new)


    def set_compressor(ratio):

        def calc_makeup_gain(fac, th=60):
            """ Estimates the make up gain for a given compression factor, that is
                a compressor ratio of "fac:1", assuming a "quasi full scale compressor"
                (threshold = -60 dB)
            """

            experimetal_divider = 1.5

            return round( -(th - th / fac) / experimetal_divider, 1)

        threshold   = -60
        factor      = round(float( ratio.split(':')[0] ), 1)
        makeup_gain = calc_makeup_gain(factor, threshold)

        cfg = PC.config.active()
        pms = cfg["processors"]["tv_compressor"]["parameters"]
        pms["threshold"]   = threshold
        pms["factor"]      = factor
        pms["makeup_gain"] = makeup_gain

        PC.config.set_active(cfg)


    # Compressor enable / disable commands
    if oper in ('on', True, 'true'):
        _bypass('compressor', False)

    elif oper in ('off', False, 'false'):
        _bypass('compressor', True)

    elif oper == 'toggle':
        new_mode = {True: False, False: True} [ _bypass('compressor') ]
        _bypass('compressor', new_mode)

    # State command
    elif oper == 'get':
        pass

    # Change ratio commands
    elif oper == 'set':
        set_compressor(ratio)

    elif oper == 'rotate':
        rotate_compressor()

    else:
        return 'not valid'

    parameters  = get_parameters()
    active      = not _bypass('compressor', 'state')

    return  {'active': active, 'parameters': parameters}

