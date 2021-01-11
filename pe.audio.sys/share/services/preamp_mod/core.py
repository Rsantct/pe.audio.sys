#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.
#
# This is based on 'pre.di.c,' a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
# 'pre.di.c' is based on 'FIRtro', a preamp and digital crossover
# https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
#
# 'pe.audio.sys' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'pe.audio.sys' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.

import os
UHOME = os.path.expanduser("~")
MAINFOLDER = f'{UHOME}/pe.audio.sys'

import sys
from socket import socket
from subprocess import Popen, check_output
import yaml
import jack
import numpy as np
from time import sleep
import threading

sys.path.append(MAINFOLDER)
from share.miscel import Fmt


# JCLI: the client interface to the JACK server ================================
tries = 15 #  15 * 1/5 s = 3 s
print( f'{Fmt.BOLD}(core) connecting to JACK ', end='' )
while tries:
    try:
        JCLI = jack.Client('core', no_start_server=True)
        break
    except:
        print( f'.', end='' )
    tries -=1
    sleep(.2)
print(Fmt.END)
if not tries:
    # BYE :-/
    raise ValueError( '(core) ERROR cannot commuticate to the JACK SOUND SERVER')


# AUX and FILES MANAGEMENT: ====================================================
def find_target_sets():
    """
        Retrieves the sets of available target curves under the share/eq folder.

                            file name:              returned set name:
        minimal name        'target_mag.dat'        'target'
        a more usual name   'xxxx_target_mag.dat'   'xxxx'

        A 'none' set name is added as default for no target eq to be applied.
    """
    def extract(x):
        """ Aux to extract a meaningful set name, examples:
                'xxxx_target_mag.dat'   will return 'xxxx'
                'target_mag.dat'        will return 'target'
        """

        if x[:6] == 'target':
            return 'target'
        else:
            x = x[:-14]

        # strip trailing unions if used
        for c in ('.', '-', '_'):
            if x[-1] == c:
                x = x[:-1]

        return x

    result = ['none']

    files = os.listdir( EQ_FOLDER )
    tfiles = [ x for x in files if ('target_mag' in x) or ('target_pha' in x) ]

    for fname in tfiles:
        set_name = extract(fname)
        if not set_name in result:
            result.append( set_name )

    return result


def get_peq_in_use():
    """ Finds out the PEQ (parametic eq) filename used by an inserted
        Ecasound sound processor, if included inside config.yml scripts.
    """
    for item in CONFIG["scripts"]:
        if type(item) == dict and 'ecasound_peq.py' in item.keys():
            return item["ecasound_peq.py"].replace('.ecs', '')
    return 'none'


def get_eq_curve(cname, state):
    """ Retrieves the tone or loudness curve.
        Tone curves depens on state bass & treble.
        Loudness compensation curve depens on the configured refSPL.
    """
    # (i) Former FIRtro curves array files xxx.dat were stored in Matlab way,
    #     so when reading them with numpy.loadtxt() it was needed to transpose
    #     and flipud in order to access to the curves data in a natural way.
    #     Currently the curves are stored in pythonic way, so numpy.loadtxt()
    #     will read directly usable data.

    # Tone eq curves are given [-span...0...-span]
    if cname == 'bass':
        bass_center_index = (EQ_CURVES["bass_mag"].shape[0] - 1) // 2
        index = int(round(state["bass"]))   + bass_center_index

    elif cname == 'treb':
        treble_center_index = (EQ_CURVES["treb_mag"].shape[0] - 1) // 2
        index = int(round(state["treble"])) + treble_center_index

    # Using the previously detected flat curve index and
    # also limiting as per the eq_loud_ceil boolean inside config.yml
    elif cname == 'loud':

        index_max   = EQ_CURVES["loud_mag"].shape[0] - 1
        index_flat  = CONFIG['refSPL']
        index_min   = 0
        if CONFIG["eq_loud_ceil"]:
            index_max = index_flat

        if state["equal_loudness"]:
            index = CONFIG['refSPL'] + state["level"]
        else:
            index = index_flat
        index = int(round(index))

        # Clamp index to the available "loudness deepness" curves set
        index = max( min(index, index_max), index_min )

    return EQ_CURVES[f'{cname}_mag'][index], \
           EQ_CURVES[f'{cname}_pha'][index]


def find_eq_curves():
    """ Scans share/eq/ and try to collect the whole set of EQ curves
        needed for the EQ stage in Brutefir
    """
    EQ_CURVES = {}
    eq_files = os.listdir(EQ_FOLDER)

    # file names ( 2x loud + 4x tones + freq = total 7 curves)
    fnames = (  'loudness_mag.dat', 'bass_mag.dat', 'treble_mag.dat',
                'loudness_pha.dat', 'bass_pha.dat', 'treble_pha.dat',
                'freq.dat' )

    # map dict to get the curve name from the file name
    cnames = {  'loudness_mag.dat'  : 'loud_mag',
                'bass_mag.dat'      : 'bass_mag',
                'treble_mag.dat'    : 'treb_mag',
                'loudness_pha.dat'  : 'loud_pha',
                'bass_pha.dat'      : 'bass_pha',
                'treble_pha.dat'    : 'treb_pha',
                'freq.dat'          : 'freqs'     }

    pendings = len(fnames)  # 7 curves
    for fname in fnames:

        # Only one file named as <fname> must be found

        if 'loudness' in fname:
            prefixedfname = f'ref_{CONFIG["refSPL"]}_{fname}'
            files = [ x for x in eq_files if prefixedfname in x]
        else:
            files = [ x for x in eq_files if fname in x]

        if files:

            if len (files) == 1:
                EQ_CURVES[ cnames[fname] ] = \
                         np.loadtxt( f'{EQ_FOLDER}/{files[0]}' )
                pendings -= 1
            else:
                print(f'(core) too much \'...{fname}\' '
                       'files under share/eq/')
        else:
            print(f'(core) ERROR finding a \'...{fname}\' '
                   'file under share/eq/')

    #if not pendings:
    if pendings == 0:
        return EQ_CURVES
    else:
        return {}


def calc_eq( state ):
    """ Calculate the eq curves to be applied in the Brutefir EQ module,
        as per the provided dictionary of state values.
    """
    zeros = np.zeros( EQ_CURVES["freqs"].shape[0] )

    # getting loudness and tones curves
    loud_mag, loud_pha = get_eq_curve( 'loud', state )
    bass_mag, bass_pha = get_eq_curve( 'bass', state )
    treb_mag, treb_pha = get_eq_curve( 'treb', state )

    # getting target curve
    target_name = state["target"]
    if target_name == 'none':
        targ_mag = zeros
        targ_pha = zeros
    else:
        if target_name != 'target':     # see doc string from find_target_sets()
            target_name += '_target'
        targ_mag = np.loadtxt( f'{EQ_FOLDER}/{target_name}_mag.dat' )
        targ_pha = np.loadtxt( f'{EQ_FOLDER}/{target_name}_pha.dat' )

    # Compose
    eq_mag = targ_mag + loud_mag * state["equal_loudness"] \
                                                + bass_mag + treb_mag

    if CONFIG["bfeq_linear_phase"]:
        eq_pha = zeros
    else:
        eq_pha = targ_pha + loud_pha * state["equal_loudness"] \
                 + bass_pha + treb_pha

    return eq_mag, eq_pha


def calc_gain( state ):
    """ Calculates the gain from:   level,
                                    ref_level_gain
                                    source gain offset
    """

    gain    = state["level"] + float(CONFIG["ref_level_gain"]) \
                             - state["lu_offset"]

    # Adding here the specific source gain:
    if state["input"] != 'none':
        gain += float( CONFIG["sources"][state["input"]]["gain"] )

    return gain


def powersave_loop( convolver_off_driver, convolver_on_driver,
                    end_loop_flag, reset_elapsed_flag ):
    """ Loops forever every 1 sec reading the dBFS level on preamp input.
        If detected signal is below NOISE_FLOOR during MAX_WAIT then stops
        Brutefir. If signal level raises, then resumes Brutefir.

        Events managed here:
        convolver_off_driver:   Will set when no detected signal
        convolver_on_driver:    Will set when detected signal
        end_loop_flag:          Will check on every loop
        reset_elapsed_flag:     Will check and clear, useful when switching
                                to a no signal source to avoid killing brutefir
                                suddenly (see Preamp.select_source#NewSource)
    """


    def sec2min(s):
        m = s // 60
        s = s % 60
        return f'{str(m).rjust(2,"0")}m{str(s).rjust(2,"0")}s'


    def read_loudness_monitor():
        # Lets use LU_M (LU Momentary) from .loudness_monitor
        try:
            with open(f'{MAINFOLDER}/.loudness_monitor', 'r') as f:
                d = yaml.safe_load( f )
                LU_M = d["LU_M"]
        except:
            LU_M = 0.0
        dBFS = LU_M - 23.0  # LU_M is referred to -23dBFS
        return dBFS


    def loudness_monitor_is_running():
        times = 10
        while times:
            try:
                check_output('pgrep -f loudness_monitor.py'.split()).decode()
                return True
            except:
                times -= 1
            sleep(1)
        return False


    # Default values:
    NOISE_FLOOR = -70
    MAX_WAIT    =  60
    # CONFIG values overrides:
    if "powersave_noise_floor" in CONFIG:
        NOISE_FLOOR = CONFIG["powersave_noise_floor"]
    if "powersave_max_wait" in CONFIG:
        MAX_WAIT = CONFIG["powersave_max_wait"]

    # Using a level meter, loudness_monitor.py is preferred,
    # if not available will use level_meter.py
    loud_mon_available = loudness_monitor_is_running()
    if loud_mon_available:
        print( f'(powersave) using \'loudness_monitor.py\'' )
    else:
        # Prepare and start a level_meter.Meter instance
        sys.path.append( f'{MAINFOLDER}/share/audiotools' )
        from level_meter import Meter
        meter = Meter(device='pre_in_loop', mode='peak', bar=False)
        meter.start()
        print( f'(powersave) using \'level_meter.py\'' )

    # Loop forever each 1 sec will check signal level
    print(f'(powersave) running')
    lowSigElapsed = 0
    while True:

        if reset_elapsed_flag.isSet():
            lowSigElapsed = 0
            reset_elapsed_flag.clear()

        # Reading level
        if loud_mon_available:
            dBFS = read_loudness_monitor()
        else:
            dBFS = meter.L

        # Level detected
        if dBFS > NOISE_FLOOR:
            if not brutefir_is_running():
                print(f'(powersave) signal detected, requesting to restart Brutefir')
                convolver_on_driver.set()
            lowSigElapsed = 0
        else:
            lowSigElapsed +=1

        # No level detected
        if dBFS < NOISE_FLOOR and lowSigElapsed >= MAX_WAIT:
            if brutefir_is_running():
                print(f'(powersave) low level during {sec2min(MAX_WAIT)}, '
                       'requesting to stop Brutefir' )
                convolver_off_driver.set()

        # Break loop
        if end_loop_flag.isSet():
            break

        sleep(1)


# BRUTEFIR MANAGEMENT: =========================================================
def bf_cli(cmd):
    """ queries commands to Brutefir
    """
    # using 'with' will disconnect the socket when done
    ans = ''
    with socket() as s:
        try:
            s.connect( ('localhost', 3000) )
            s.send( f'{cmd}; quit;\n'.encode() )
            while True:
                tmp = s.recv(1024).decode()
                if not tmp:
                    break
                ans += tmp
            s.close()
        except:
            print( f'(core) unable to connect to Brutefir:3000' )
    return ans


def bf_set_gains( state ):
    """ - Adjust Brutefir gain at filtering f.lev.xx stages as per the
          provided state values and configured reference levels.
        - Routes channels to listening modes 'mid' (mono) or 'side' (L-R).
        - Manages the 'solo' feature.

        (i) Midside (formerly mono) is implemented by routing and mixing
            from the inputs to the first filter stages (f.lev.Ch):

                      f.lev.L
        in.L  --------  LL
               \  ____  LR
                \/
                /\____
               /        RL
        in.R  --------  RR
                      f.lev.R
    """

    dB_gain    = calc_gain( state )
    dB_balance = state["balance"]
    dB_gain_L  = dB_gain - dB_balance / 2.0
    dB_gain_R  = dB_gain + dB_balance / 2.0

    # Normalize the polarity string
    if state["polarity"] == '+':
        state["polarity"] = '++'
    elif state["polarity"] == '-':
        state["polarity"] = '--'

    # Prepare some unity multipliers:
    pola_L = {'+': 1, '-': -1}          [ state["polarity"][0] ]
    pola_R = {'+': 1, '-': -1}          [ state["polarity"][1] ]
    solo_L = {'off': 1, 'l': 1, 'r': 0} [ state["solo"]        ]
    solo_R = {'off': 1, 'l': 0, 'r': 1} [ state["solo"]        ]
    mute   = {True: 0, False: 1}        [ state["muted"]       ]

    # Compute gain from dB to a multiplier, then apply multipliers.
    # Multiplier is an alternative to dB attenuation available
    # on 'cfia' and 'cffa' commands syntax.
    m_gain_L = 10 ** (dB_gain_L / 20.0) * mute * pola_L * solo_L
    m_gain_R = 10 ** (dB_gain_R / 20.0) * mute * pola_R * solo_R

    # Compute the final gains as per the midside setting:
    # mid ==> L + R (mono)
    if   state["midside"] == 'mid':
        LL = m_gain_L * 0.5; LR = m_gain_R *  0.5
        RL = m_gain_L * 0.5; RR = m_gain_R *  0.5

    # side ==> L - R. No panned and in-phase sounds will disappear
    #                 if your stereo image works well
    elif state["midside"] == 'side':
        LL = m_gain_L * 0.5; LR = m_gain_R * -0.5
        RL = m_gain_L * 0.5; RR = m_gain_R * -0.5

    # off ==> L , R  (regular stereo)
    elif state["midside"] == 'off':
        LL = m_gain_L * 1.0; LR = m_gain_R *  0.0
        RL = m_gain_L * 0.0; RR = m_gain_R *  1.0

    Lcmd = f'cfia "f.lev.L" "in.L" m{LL} ; cfia "f.lev.L" "in.R" m{LR}'
    Rcmd = f'cfia "f.lev.R" "in.L" m{RL} ; cfia "f.lev.R" "in.R" m{RR}'

    bf_cli( f'{Lcmd}; {Rcmd}' )


def bf_set_eq( eq_mag, eq_pha ):
    """ Adjust the Brutefir EQ module,
        also will dump an EQ graph
    """
    global last_eq_mag

    freqs = EQ_CURVES["freqs"]
    mag_pairs = []
    pha_pairs = []
    i = 0
    for freq in freqs:
        mag_pairs.append( str(freq) + '/' + str(round(eq_mag[i], 3)) )
        pha_pairs.append( str(freq) + '/' + str(round(eq_pha[i], 3)) )
        i += 1
    mag_str = ', '.join(mag_pairs)
    pha_str = ', '.join(pha_pairs)

    bf_cli('lmc eq "c.eq" mag '   + mag_str)
    bf_cli('lmc eq "c.eq" phase ' + pha_str)

    # Keeping the global updated
    if not (last_eq_mag == eq_mag).all():
        last_eq_mag = eq_mag
        # Dumping the EQ graph to a png file
        if CONFIG["web_config"]["show_graphs"]:
            bfeq2png.do_graph( freqs, eq_mag,
                               is_lin_phase=CONFIG["bfeq_linear_phase"] )


def bf_read_eq():
    """ Returns the current freqs, magnitude and phase
        as rendered into the Brutefir eq coeff.
    """
    ans = bf_cli('lmc eq "c.eq" info;')
    for line in ans.split('\n'):
        if line.strip()[:5] == 'band:':
            freq = line.split()[1:]
        if line.strip()[:4] == 'mag:':
            mag  = line.split()[1:]
        if line.strip()[:6] == 'phase:':
            pha  = line.split()[1:]

    return  np.array(freq).astype(np.float), \
            np.array(mag).astype(np.float),  \
            np.array(pha).astype(np.float)


def bf_set_drc( drcID ):
    """ Changes the FIR for DRC at runtime
    """

    if drcID == 'none':
        cmd = ( f'cfc "f.drc.L" -1 ;'
                 'cfc "f.drc.R" -1 ;' )
    else:
        cmd = ( f'cfc "f.drc.L" "drc.L.{drcID}";'
                f'cfc "f.drc.R" "drc.R.{drcID}";' )

    bf_cli( cmd )


def bf_set_xo( ways, xo_coeffs, xoID ):
    """ Changes the FIRs for XOVER at runtime
    """

    # example:
    #   ways:
    #               f.lo.L f.hi.L f.lo.R f.hi.R f.sw
    #   xo_coeffs:
    #               xo.hi.L.mp  xo.hi.R.lp
    #               xo.hi.R.mp  xo.hi.L.lp
    #               xo.lo.mp    xo.lo.lp
    #               xo.sw.mp    xo.sw.lp
    #   xo_sets:
    #               mp          lp
    # NOTICE:
    #   This example has dedicated coeff FIRs for hi.L and hi.R,
    #   so when seleting the appropiate coeff we will try 'best matching'

    def find_best_match_coeff(way):

        found = ''
        # lets try matching coeff with way[2:] including the channel id
        for coeff in xo_coeffs:
            if way[2:] in coeff[3:] and xoID == coeff.split('.')[-1]:
                found = coeff

        # if not matches, then try just the way[2:4], e.g. 'lo'
        if not found:
            for coeff in xo_coeffs:
                if way[2:4] in coeff[3:] and xoID == coeff.split('.')[-1]:
                    found = coeff

        return found

    cmd = ''
    for way in ways:
        BMcoeff = find_best_match_coeff(way)
        cmd += f'cfc "{way}" "{BMcoeff}"; '

    #print (cmd)
    bf_cli( cmd )


def get_brutefir_config(prop):
    """ returns a property from brutefir_config file
        (BETA: currently only works for ludspeaker ways)
    """
    with open(f'{LSPK_FOLDER}/brutefir_config', 'r') as f:
        lines = f.read().split('\n')

    if prop == 'ways':
        ways = []
        for line in [ x for x in lines if x and 'filter' in x.strip().split() ]:
            if '"f.eq.' not in line and '"f.drc.' not in line and \
                                              line.startswith('filter'):
                way = line.split()[1].replace('"', '')
                ways.append( way )
        return ways
    else:
        return []


def brutefir_is_running():
    if JCLI.get_ports('brutefir'):
        return True
    else:
        return False


def bf_get_in_connections():
    bf_inputs = JCLI.get_ports('brutefir', is_input=True)
    src_ports = []
    for p in bf_inputs:
        srcs = JCLI.get_all_connections(p)
        for src in srcs:
            src_ports.append( src )
    if src_ports:
        return src_ports
    else:
        return ['pre_in_loop:output_1', 'pre_in_loop:output_2']


def restart_and_reconnect_brutefir(bf_sources=[]):
    """ Restarts Brutefir as external process (Popen),
        then check Brutefir spawn connections to system ports,
        then reconnects Brutefir inputs.
        (i) Notice that Brutefir inputs can have sources
            other than 'pre_in_loop:...'
    """
    warnings=''

    # Restarts Brutefir (external process)
    os.chdir(LSPK_FOLDER)
    Popen('brutefir brutefir_config', shell=True)
    os.chdir(UHOME)
    sleep(1)  # wait a bit for Brutefir to be running

    # Wait for Brutefir to autoconnect its :out_X ports to system: ports
    tries = 120     # ~ 60 sec
    while tries:

        # Showing progress every 3 sec
        if tries % 6 == 0:
            print(  f'{Fmt.BLUE}(core) waiting for Brutefir ports '
                    f'{"."*int((120-tries)/6)}{Fmt.END}')

        # Getting the bf out ports list
        bf_out_ports = JCLI.get_ports('brutefir', is_output=True)

        # Ensuring that ports are available
        if len(bf_out_ports) < 2:
            sleep(.5)
            tries -= 1  # do not forget this decrement before 'continue'
            continue

        # Counting if all bf_out_ports are properly bonded to system ports
        n = 0
        for p in bf_out_ports:
            conns = JCLI.get_all_connections(p)
            n += len(conns)
        if n == len(bf_out_ports):
            # We are done ;-)
            break

        tries -= 1
        sleep(.5)

    if not tries:
        warnings += ' PROBLEM RUNNING BRUTEFIR :-('

    # Wait for brutefir input ports to be available
    tries = 50      # ~ 10 sec
    while tries:
        bf_in_ports = JCLI.get_ports('brutefir', is_input=True)
        if len(bf_in_ports) >= 2:
            break
        else:
            tries -= 1
            sleep(.2)
    if not tries:
        warnings += ' Brutefir ERROR getting jack ports available.'

    # A safe wait to avoid early connections failures
    sleep(.5)

    # Restore input connections
    for a, b in zip(bf_sources, bf_in_ports):
        res = jack_connect(a, b)
        if res != 'done':
            warnings += f' {res}'

    if not warnings:
        return 'done'
    else:
        return warnings


# JACK MANAGEMENT: =============================================================
def jack_connect(p1, p2, mode='connect', wait=1):
    """ Low level tool to connect / disconnect a pair of ports,
        by retriyng for a while
    """
    # Will retry during <wait> seconds, this is useful when a
    # jack port exists but it is still not active,
    # for instance Brutefir ports takes some seconds to be active.

    wait = int(wait)
    # will retry every second
    while wait > 0 :
        try:
            if 'dis' in mode or 'off' in mode:
                JCLI.disconnect(p1, p2)
            else:
                JCLI.connect(p1, p2)
            return 'done'
        except jack.JackError as e:
            print( f'(core.jack_connect) Exception: {e}' )
            return e
        wait -= 1
        sleep(1)


def jack_connect_bypattern( cap_pattern, pbk_pattern, mode='connect', wait=1 ):
    """ High level tool to connect/disconnect a given port name patterns
    """
    # Try to get ports by a port name pattern
    cap_ports = JCLI.get_ports( cap_pattern, is_output=True )
    pbk_ports = JCLI.get_ports( pbk_pattern, is_input=True )

    # If not found, it can be an ALIAS pattern
    # (if used, jackd -Ln loopback ports will be aliased with the source name)
    if not cap_ports:
        loopback_cap_ports = JCLI.get_ports( 'loopback', is_output=True )
        for p in loopback_cap_ports:
            # A port can have 2 alias, our is the 2nd one.
            if cap_pattern in p.aliases[1]:
                cap_ports.append(p)
    if not pbk_ports:
        loopback_pbk_ports = JCLI.get_ports( 'loopback', is_input=True )
        for p in loopback_pbk_ports:
            if pbk_pattern in p.aliases[1]:
                pbk_ports.append(p)

    #print('CAPTURE  ====> ', cap_ports)  # DEBUG
    #print('PLAYBACK ====> ', pbk_ports)
    errors = ''
    if not cap_ports:
        tmp = f'cannot find jack port "{cap_pattern}" '
        print(f'(core) {tmp}')
        errors += tmp
    if not pbk_ports:
        tmp = f'cannot find jack port "{pbk_pattern}" '
        print(f'(core) {tmp}')
        errors += tmp
    if errors:
        return errors

    mode = 'disconnect' if ('dis' in mode or 'off' in mode) else 'connect'
    for cap_port, pbk_port in zip(cap_ports, pbk_ports):
        job_jc = threading.Thread( target=jack_connect,
                                   args=(cap_port, pbk_port, mode, wait) )
        job_jc.start()
    return 'ordered'


def jack_clear_preamp():
    """ Force clearing ANY clients, no matter what input was selected
    """
    preamp_ports = JCLI.get_ports('pre_in_loop', is_input=True)
    for preamp_port in preamp_ports:
        for client in JCLI.get_all_connections(preamp_port):
            jack_connect( client, preamp_port, mode='off' )


# THE PREAMP: AUDIO PROCESSOR, SELECTOR, and SYSTEM STATE KEEPER ===============
def init_audio_settings():
    """ Forcing if indicated on config.yml or restoring last state from disk
    """

    def try_init(prop):
        """ Try to set a value defined under CONFIG['on_init'][prop]
            Returns a warning or an empty string
        """
        value = CONFIG["on_init"][prop]

        # Skipping if not defined
        if value is None:
            return ''

        # Manage the special key 'max_level'
        if prop == 'max_level':
            value = min( value, preamp.state["level"] )
            prop = 'level'

        func = {
                'xo':               convolver.set_xo,
                'drc':              convolver.set_drc,
                'input':            preamp.select_source,
                'target':           preamp.set_target,
                'level':            preamp.set_level,
                'muted':            preamp.set_mute,
                'bass':             preamp.set_bass,
                'treble':           preamp.set_treble,
                'balance':          preamp.set_balance,
                'equal_loudness':   preamp.set_equal_loudness,
                'lu_offset':        preamp.set_lu_offset,
                'midside':          preamp.set_midside,
                'polarity':         preamp.set_polarity,
                'solo':             preamp.set_solo
                }[prop]

        # Some keys can be formerly named:
        if prop == 'xo':
            state_prop = 'xo_set'
        elif prop == 'drc':
            state_prop = 'drc_set'
        else:
            state_prop = prop

        # Processing
        warning = ''
        if func( value ) == 'done':
            preamp.state[state_prop] = value
        else:
            warning = f'{Fmt.RED}bad {prop}:{value}{Fmt.END}'
            # Using last state
            value = preamp.state[state_prop]
            if func( value ) != 'done':
                # This should never happen:
                warning = f'{Fmt.RED}{Fmt.BOLD} BAD STATE {prop}:{value}{Fmt.END}'

        return warning


    # temporary Preamp and Convolver instances
    preamp    = Preamp()
    convolver = Convolver()
    warnings  = ''

    # Iterate over config.on_init:
    for prop in CONFIG['on_init']:
        warning = try_init(prop)
        if warning:
            warnings += f'{warning}, '

    # saving state to disk, then closing tmp instances
    preamp.save_state()
    del(convolver)
    del(preamp)

    if not warnings:
        print( f'{Fmt.BLUE}(core.on_init) done.{Fmt.END}' )
        return 'done'
    else:
        print( f'(core.on_init) {warnings[:-2]}' )
        return warnings[:-2]


def connect_monitors():
    """ Connect source monitors to preamp-loop
    """
    if CONFIG["source_monitors"]:
        for monitor in CONFIG["source_monitors"]:
            jack_connect_bypattern('pre_in_loop', monitor, wait=60)


class Preamp(object):
    """ attributes:

            state           state dictionary
            inputs          the available inputs dict.
            target_sets     target curves available under the 'eq' folder
            bass_span       available span for tone curves
            treble_span
            gain_max        max authorised gain
            balance_max     max authorised balance

        methods:

            save_state      save state dict to disk

            select_source
            set_level
            set_balance
            set_bass
            set_treble
            set_lu_offset
            set_equal_loudness
            set_target
            set_solo
            set_mute
            set_midside

            get_state
            get_inputs
            get_target_sets
            get_eq

            convolver       stops or resume Brutefir (energy saving)

    """


    # Preamp INIT
    def __init__(self):

        # The available inputs
        self.inputs = CONFIG["sources"]
        # The state dictionary
        self.state = yaml.safe_load( open(STATE_PATH, 'r') )
        self.state["convolver_runs"] = brutefir_is_running()
        # will add some informative values:
        self.state["loudspeaker"] = CONFIG["loudspeaker"]
        self.state["loudspeaker_ref_SPL"] = CONFIG["refSPL"]
        self.state["peq_set"] = get_peq_in_use()
        self.state["fs"] = JCLI.samplerate
        # The target curves available under the 'eq' folder
        self.target_sets = find_target_sets()
        # The available span for tone curves
        self.bass_span   = int( (EQ_CURVES["bass_mag"].shape[0] - 1) / 2 )
        self.treble_span = int( (EQ_CURVES["treb_mag"].shape[0] - 1) / 2 )
        # Max authorised gain
        self.gain_max    = float(CONFIG["gain_max"])
        # Max authorised balance
        self.balance_max = float(CONFIG["balance_max"])
        # Initiate brutefir input connected ports (used from switch_convolver)
        self.bf_sources = bf_get_in_connections()

        # Powersave
        #   State file info
        self.state["powersave"] = False
        #
        #   Powersave loop: breaking flag
        self.ps_end = threading.Event()
        #
        #   Powersave loop:reset elapsed low level detected counter flag
        self.ps_reset_elapsed = threading.Event()
        #
        #   Convolver driving events
        def wait_PS_convolver_off():
            """ Event handler for convolver switch off requests
            """
            while True:
                # waiting ...
                self.ps_convolver_off.wait()
                print(f'(core) Thread \'waits for convolver OFF\' received event')
                self.ps_convolver_off.clear()
                self.switch_convolver('off')
        #
        def wait_PS_convolver_on():
            """ Event handler for convolver switch on requests
            """
            while True:
                # waiting ...
                self.ps_convolver_on.wait()
                print(f'(core) Thread \'waits for convolver ON\' received event')
                self.ps_convolver_on.clear()
                self.switch_convolver('on')
        #
        self.ps_convolver_off = threading.Event()
        self.ps_convolver_on  = threading.Event()
        t1 = threading.Thread( name='waits for convolver OFF',
                               target=wait_PS_convolver_off )
        t2 = threading.Thread( name='waits for convolver ON',
                               target=wait_PS_convolver_on )
        t1.start()
        t2.start()
        self._print_threads()


    # Preamp METHODS:
    # (i) Remember to return some result from any method below.
    #     Also notice that we use *dummy to accommodate the preamp.py parser
    #     mechanism wich always will include two arguments for any Preamp call.


    def _print_threads(self):
        """ Console info about active threads
        """
        print( f'(core) {threading.activeCount()} threads:' )
        for i, t in enumerate(threading.enumerate()):
            print(' ', i, t.name)
        return 'done'


    def powersave(self, mode, *dummy):
        """ on:  Initiate a threaded powersave_loop signal monitor job.
            off: Flags to break the loop then will termitate the threaded job.
        """

        if mode == 'on':
            ps_job = threading.Thread( name='powersave LOOP',
                                       target=powersave_loop,
                                       args=( self.ps_convolver_off,
                                              self.ps_convolver_on,
                                              self.ps_end,
                                              self.ps_reset_elapsed ) )
            ps_job.start()
            self.state["powersave"] = True

        elif mode == 'off':
            self.ps_end.set()
            # To ensure that powersave_loop 1 sec cicle can detect
            # the ps_end flag, then terminate itself.
            sleep(2)
            self.ps_end.clear()
            self.state["powersave"] = False

        else:
            return 'bad option'

        self._print_threads()

        return 'done'


    def switch_convolver( self, mode, *dummy ):

        result = 'nothing done'

        if mode == 'off':

            if brutefir_is_running():
                self.bf_sources = bf_get_in_connections()
                Popen(f'pkill -f brutefir', shell=True)
                sleep(2)
                print(f'(core) STOOPING BRUTEFIR (!)')
                result = 'done'

        elif mode == 'on':

            if not brutefir_is_running():

                # This avoids that powersave loop kills Brutefir
                self.ps_reset_elapsed.set()

                result = restart_and_reconnect_brutefir(self.bf_sources)
                if result == 'done':
                    self._validate( self.state ) # this includes mute
                    c = Convolver()
                    c.set_xo ( self.state["xo_set"]  )
                    c.set_drc( self.state["drc_set"] )
                    del( c )
                else:
                    result = f'PANIC: {result}'

        else:
            result = 'bad option'

        self.save_state()

        return result


    def _validate( self, candidate ):
        """ Validates that the given 'candidate' (new state dictionary)
            does not exceed gain limits
        """
        gmax            = self.gain_max
        gain            = calc_gain( candidate )
        eq_mag, eq_pha  = calc_eq( candidate )
        bal             = candidate["balance"]

        headroom = gmax - gain - np.max(eq_mag) - np.abs(bal / 2.0)

        # (i)
        # 'config.yml' SOURCE's GAIN are set arbitrarily at the USER's OWN RISK,
        # so we exclude it from the headroom calculation.
        # So although 'gmax: 0.0' (this is digital domain alowed gain),
        # if a source had gain: 6.0, the real 'gain' on Brutefir level stage
        # can be up to +6.0 dB because of this consideration.
        if candidate["input"] != 'none':
            try:
                input_gain = float( CONFIG["sources"][candidate["input"]]["gain"] )
            except:
                input_gain = 0.0
        else:
            input_gain = 0.0

        headroom += input_gain

        if headroom >= 0:
            # APPROVED
            bf_set_gains( candidate )
            bf_set_eq( eq_mag, eq_pha )
            self.state = candidate
            return 'done'
        else:
            # REFUSED
            return 'not enough headroom'


    def save_state(self):
        self.state["convolver_runs"] = brutefir_is_running()
        with open(STATE_PATH, 'w') as f:
            yaml.safe_dump( self.state, f, default_flow_style=False )


    def get_state(self, *dummy):
        return self.state


    def get_target_sets(self, *dummy):
        return self.target_sets


    def set_level(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate["level"] += round(float(value), 2)
        else:
            candidate["level"] =  round(float(value), 2)
        return self._validate( candidate )


    def set_balance(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate["balance"] += round(float(value), 2)
        else:
            candidate["balance"] =  round(float(value), 2)
        if abs(candidate["balance"]) <= self.balance_max:
            return self._validate( candidate )
        else:
            return 'too much'


    def set_bass(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate["bass"] += round(float(value), 2)
        else:
            candidate["bass"] =  round(float(value), 2)
        if abs(candidate["bass"]) <= self.bass_span:
            return self._validate( candidate )
        else:
            return 'too much'


    def set_treble(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate["treble"] += round(float(value), 2)
        else:
            candidate["treble"] =  round(float(value), 2)
        if abs(candidate["treble"]) <= self.treble_span:
            return self._validate( candidate )
        else:
            return 'too much'


    def set_lu_offset(self, value, relative=False):
        candidate = self.state.copy()
        # this try if intended just to validate the given value
        try:
            if relative:
                candidate["lu_offset"] += round(float(value), 2)
            else:
                candidate["lu_offset"] =  round(float(value), 2)
            return self._validate( candidate )
        except:
            return 'bad value'


    def set_equal_loudness(self, value, *dummy):
        candidate = self.state.copy()
        if type(value) == bool:
            value = str(value)
        try:
            value = { 'on': True , 'off': False,
                      'true': True, 'false': False,
                      'toggle': {True: False, False: True
                                 }[self.state["equal_loudness"]]
                     } [ value.lower() ]
            candidate["equal_loudness"] = value
            return self._validate( candidate )
        except:
            return 'bad option'


    def set_target(self, value, *dummy):
        candidate = self.state.copy()
        if value in self.target_sets:
            candidate["target"] = value
            return self._validate( candidate )
        else:
            return f'target \'{value}\' not available'


    def set_solo(self, value, *dummy):
        if value.lower() in ('off', 'l', 'left', 'r', 'right'):
            if value.lower() == 'left':
                value = 'l'
            if value.lower() == 'right':
                value = 'r'
            self.state["solo"] = value.lower()
            bf_set_gains( self.state )
            return 'done'
        else:
            return 'bad option'


    def set_polarity(self, value, *dummy):
        if value in ('+', '-', '++', '--', '+-', '-+'):
            self.state["polarity"] = value.lower()
            bf_set_gains( self.state )
            return 'done'
        else:
            return 'bad option'


    def set_mute(self, value, *dummy):
        if type(value) == bool:
            value = str(value)
        try:
            if value.lower() in ('false', 'true', 'off', 'on', 'toggle'):
                value = { 'false': False, 'off': False,
                          'true' : True,  'on' : True,
                          'toggle': {False: True, True: False}
                                                 [ self.state["muted"] ]
                        } [ value.lower() ]
                self.state["muted"] = value
                bf_set_gains( self.state )
                return 'done'
        except:
            return 'bad option'


    def set_midside(self, value, *dummy):
        if value.lower() in ( 'mid', 'side', 'off' ):
            self.state["midside"] = value.lower()
            bf_set_gains( self.state )
        else:
            return 'bad option'
        return 'done'


    def get_eq(self, *dummy):
        freq, mag , pha = bf_read_eq()
        return { 'band': freq.tolist(), 'mag': mag.tolist(),
                                        'pha': pha.tolist() }


    def select_source(self, source, *dummy):

        def try_select(source):
            """ this is the source selector """
            w = '' # warnings

            # clearing 'preamp' connections
            jack_clear_preamp()

            # connecting the new SOURCE to PREAMP input
            current_source = self.state['input']
            res = jack_connect_bypattern(CONFIG["sources"][source]["capture_port"],
                                         'pre_in')

            if res != 'ordered':
                w += res

            # Trying to set the desired xo and drc for this source
            c = Convolver()
            try:
                xo = CONFIG["sources"][source]["xo"]
                if xo and c.set_xo( xo ) == 'done':
                    self.state["xo_set"] = xo
                elif xo:
                    if w:
                        w += '; '
                    w += f'\'xo:{xo}\' in \'{source}\' is not valid'
            except:
                pass
            try:
                drc = CONFIG["sources"][source]["drc"]
                if drc and c.set_drc( drc ) == 'done':
                    self.state["drc_set"] = drc
                elif drc:
                    if w:
                        w += '; '
                    w += f'\'drc:{xo}\' in \'{source}\' is not valid'
            except:
                pass
            del(c)

            # end of trying to select the source
            if not w:
                return 'done'
            else:
                return w # warnings

        def on_change_input_behavior(candidate):
            try:
                for option, value in CONFIG["on_change_input"].items():
                    if value is not None:
                        candidate[option] = value
            except:
                print('(config.yml) missing \'on_change_input\' options')
            return candidate

        result = 'nothing done'

        # Source = 'none'
        if source == 'none':
            jack_clear_preamp()
            self.state["input"] = source
            result = 'done'

        # Bad source
        elif source not in self.inputs:
            result = f'unknown source \'{source}\''

        # New source
        else:
            result = try_select(source)
            self.state["input"] = source
            candidate = self.state.copy()
            # Global audio settings on change input, but ensure the convolver
            # is running before applying audio settings.
            if not self.state["convolver_runs"]:
                self.ps_reset_elapsed.set()
                self.switch_convolver('on')
            candidate = on_change_input_behavior(candidate)
            # Some source specific audio settings overrides global settings
            # LU offset
            if 'lu_offset' in CONFIG["sources"][source]:
                candidate["lu_offset"] = \
                               CONFIG["sources"][source]["lu_offset"]
            # Target eq curve
            if 'target' in CONFIG["sources"][source]:
                candidate["target"] = CONFIG["sources"][source]["target"]
            self._validate( candidate )

        return result


    def get_inputs(self, *dummy):
        return [ x for x in self.inputs.keys() ]


# THE CONVOLVER: DRC and XO Brutefir stages management =========================
class Convolver(object):
    """ attributes:

            drc_coeffs      list of pcm FIRs for DRC
            xo_coeffs       list of pcm FIRs for XOVER
            drc_sets        sets of FIRs for DRC
            xo_sets         sets of FIRs for XOVER
            ways            filtering stages (loudspeaker ways)

        methods:

            set_drc
            set_xo

            get_drc_sets
            get_xo_sets
    """


    def __init__(self):

        # DRC pcm files must be named:
        #    drc.X.DRCSETNAME.pcm
        #
        #       where X must be L | R
        #
        # XO pcm files must be named:
        #   xo.XX[.C].XOSETNAME.pcm
        #
        #       where XX must be:     fr | lo | mi | hi | sw
        #       and channel C can be:  L | R  (optional)
        #
        #       Using C allows to have dedicated FIR per channel

        files   = os.listdir(LSPK_FOLDER)
        coeffs  = [ x.replace('.pcm', '') for x in files ]
        self.drc_coeffs = [ x for x in coeffs if x[:4] == 'drc.'  ]
        self.xo_coeffs  = [ x for x in coeffs if x[:3] == 'xo.'   ]
        #print('\nxo_coeffs:', xo_coeffs) # debug

        # The available DRC sets
        self.drc_sets = []
        for drc_coeff in self.drc_coeffs:
            drcSetName = drc_coeff[6:]
            if drcSetName not in self.drc_sets:
                self.drc_sets.append( drcSetName )

        # The available XO sets, i.e the last part of a xo_coeff
        self.xo_sets = []
        for xo_coeff in self.xo_coeffs:
            xoSetName = xo_coeff.split('.')[-1]
            if xoSetName not in self.xo_sets:
                self.xo_sets.append( xoSetName )

        # Ways are the XO filter stages definded inside brutefir_config
        # 'f.WW.C' where WW:fr|lo|mi|hi|sw and C:L|R
        self.ways = get_brutefir_config('ways')

        # debug
        #print('drc_sets:', self.drc_sets)
        #print('xo_sets:', self.xo_sets)
        #print('ways:', self.ways)

    # Bellow we use *dummy to accommodate the preamp.py parser mechanism
    # wich always will include two arguments for any function call.


    def set_drc(self, drc, *dummy):
        if drc in self.drc_sets or drc == 'none':
            bf_set_drc( drc )
            return 'done'
        else:
            return f'drc set \'{drc}\' not available'


    def set_xo(self, xo_set, *dummy):
        if xo_set in self.xo_sets:
            bf_set_xo( self.ways, self.xo_coeffs, xo_set )
            return 'done'
        else:
            return f'xo set \'{xo_set}\' not available'


    def get_drc_sets(self, *dummy):
        return self.drc_sets


    def get_xo_sets(self, *dummy):
        return self.xo_sets


# COMMON USE VARIABLES: ========================================================
CONFIG_PATH = f'{MAINFOLDER}/config.yml'
CONFIG      = yaml.safe_load(open(CONFIG_PATH, 'r'))

if CONFIG["web_config"]["show_graphs"]:
    sys.path.append ( os.path.dirname(__file__) )
    import bfeq2png

LSPK_FOLDER = f'{MAINFOLDER}/loudspeakers/{CONFIG["loudspeaker"]}'
STATE_PATH  = f'{MAINFOLDER}/.state.yml'
EQ_FOLDER   = f'{MAINFOLDER}/share/eq'

EQ_CURVES   = find_eq_curves()
if not EQ_CURVES:
    print( '(core) ERROR loading EQ_CURVES from share/eq/' )
    sys.exit()

# Aux global to avoid dumping magnitude graph if no changed
last_eq_mag = np.zeros( EQ_CURVES["freqs"].shape[0] )
