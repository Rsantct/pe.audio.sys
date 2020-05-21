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
import sys
from socket import socket
import subprocess as sp
import yaml
import jack
import numpy as np
from time import sleep
import threading

sys.path.append (os.path.dirname(__file__) )
import bfeq2png

# AUX and FILES MANAGEMENT: ============================================
def find_target_sets():
    """ Returns the uniques target filenames w/o the suffix
        _mag.dat or _pha.dat.
        Also will add 'none' as an additional set.
    """
    result = ['none']
    files = os.listdir( EQ_FOLDER )
    tmp = [ x for x in files if x[-14:-7] == 'target_'  ]
    for x in tmp:
        if not x[:-8] in result:
            result.append( x[:-8] )
    return result


def get_peq_in_use():
    """ Finds out the PEQ (parametic eq) filename used by an inserted
        Ecasound sound processor, if included inside config.yml scripts.
    """
    for item in CONFIG['scripts']:
        if type(item) == dict and 'ecasound_peq.py' in item.keys():
            return item["ecasound_peq.py"].replace('.ecs', '')
    return 'none'


def get_eq_curve(curv, state):
    """ Retrieves the tone or loudness curve.
        Tone curves depens on state bass & treble.
        Loudness compensation curve depens on the target level dBrefSPL.
    """
    # Tone eq curves are provided in reverse order [+6...0...-6]
    if curv == 'bass':

        bass_center_index = EQ_CURVES['bass_mag'].shape[1] // 2
        index =  bass_center_index - int(round(state['bass']))

    elif curv == 'treb':

        treble_center_index = EQ_CURVES['treb_mag'].shape[1] // 2
        index = treble_center_index - int(round(state['treble']))

    # Using the previously detected flat curve index and
    # also limiting as per the loud_ceil boolean inside config.yml
    elif curv == 'loud':

        # (i)
        #  Former FIRtro curves indexes have a reverse order, that is:
        #  Curves at index above the flat one are applied to compensate
        #  when level is below ref SPL (level 0.0), and vice versa,
        #  curves at index below the flat one are for levels above reference.
        index_max   = EQ_CURVES['loud_mag'].shape[1] - 1
        index_flat  = LOUD_FLAT_CURVE_INDEX
        if CONFIG['loud_ceil']:
            index_min = index_flat
        else:
            index_min   = 0

        if state['loudness_track']:
            index = index_flat - state['level']
        else:
            index = index_flat
        index = int(round(index))

        # Clamp index to the available "loudness deepness" curves set
        index = max( min(index, index_max), index_min )

    return EQ_CURVES[f'{curv}_mag'][ : , index], \
           EQ_CURVES[f'{curv}_pha'][ : , index]


def find_eq_curves():
    """ Scans share/eq/ and try to collect the whole set of EQ curves
        needed for the EQ stage in Brutefir
    """
    EQ_CURVES = {}
    eq_files = os.listdir(EQ_FOLDER)

    fnames = (  'loudness_mag.dat', 'bass_mag.dat', 'treble_mag.dat',
                'loudness_pha.dat', 'bass_pha.dat', 'treble_pha.dat',
                'freq.dat' )

    cnames = {  'loudness_mag.dat'  : 'loud_mag',
                'bass_mag.dat'      : 'bass_mag',
                'treble_mag.dat'    : 'treb_mag',
                'loudness_pha.dat'  : 'loud_pha',
                'bass_pha.dat'      : 'bass_pha',
                'treble_pha.dat'    : 'treb_pha',
                'freq.dat'          : 'freqs'     }

    # pendings curves to find ( freq + 2x loud + 4x tones = 7 )
    pendings = len(fnames)
    for fname in fnames:

        # Only one file named as <fname> must be found
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

    if not pendings:
        return EQ_CURVES
    else:
        return {}


def find_loudness_flat_curve_index():
    """ find flat curve inside xxx_loudness_mag.dat
    """
    index_max   = EQ_CURVES['loud_mag'].shape[1] - 1
    index_flat = -1
    for i in range(index_max):
        if np.sum( abs(EQ_CURVES['loud_mag'][ : , i]) ) <= 0.1:
            index_flat = i
            break
    return index_flat


def calc_eq( state ):
    """ Calculate the eq curves to be applied in the Brutefir EQ module,
        as per the provided dictionary of state values.
    """
    loud_mag, loud_pha = get_eq_curve( 'loud', state )
    bass_mag, bass_pha = get_eq_curve( 'bass', state )
    treb_mag, treb_pha = get_eq_curve( 'treb', state )

    target_name = state['target']
    if target_name == 'none':
        targ_mag = np.zeros( EQ_CURVES['freqs'].shape[0] )
        targ_pha = np.zeros( EQ_CURVES['freqs'].shape[0] )
    else:
        targ_mag = np.loadtxt( f'{EQ_FOLDER}/{target_name}_mag.dat' )
        targ_pha = np.loadtxt( f'{EQ_FOLDER}/{target_name}_pha.dat' )

    eq_mag = targ_mag + loud_mag * state['loudness_track'] \
                                                + bass_mag + treb_mag
    eq_pha = targ_pha + loud_pha * state['loudness_track'] \
                                                + bass_pha + treb_pha

    return eq_mag, eq_pha


def calc_gain( state ):
    """ Calculates the gain from:   level,
                                    ref_level_gain
                                    source gain offset
    """
    gain    = state['level'] + float(CONFIG['ref_level_gain']) \
                             - state['loudness_ref']
    if state['input'] != 'none':
        gain += float( CONFIG['sources'][state['input']]['gain'] )
    return gain


# BRUTEFIR MANAGEMENT: =================================================
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
    dB_balance = state['balance']
    dB_gain_L  = dB_gain - dB_balance / 2.0
    dB_gain_R  = dB_gain + dB_balance / 2.0

    # Normalize the polarity string
    if state['polarity'] == '+':
        state['polarity'] = '++'
    elif state['polarity'] == '-':
        state['polarity'] = '--'

    # Prepare some unity multipliers:
    pola_L = {'+': 1, '-': -1}          [ state['polarity'][0] ]
    pola_R = {'+': 1, '-': -1}          [ state['polarity'][1] ]
    solo_L = {'off': 1, 'l': 1, 'r': 0} [ state['solo']        ]
    solo_R = {'off': 1, 'l': 0, 'r': 1} [ state['solo']        ]
    mute   = {True: 0, False: 1}        [ state['muted']       ]

    # Compute gain from dB to a multiplier, then apply multipliers.
    # Multiplier is an alternative to dB attenuation available
    # on 'cfia' and 'cffa' commands syntax.
    m_gain_L = 10 ** (dB_gain_L / 20.0) * mute * pola_L * solo_L
    m_gain_R = 10 ** (dB_gain_R / 20.0) * mute * pola_R * solo_R

    # Compute the final gains as per the midside setting:
    # mid ==> L + R (mono)
    if   state['midside'] == 'mid':
        LL = m_gain_L * 0.5; LR = m_gain_R *  0.5
        RL = m_gain_L * 0.5; RR = m_gain_R *  0.5

    # side ==> L - R. No panned and in-phase sounds will disappear
    #                 if your stereo image works well
    elif state['midside'] == 'side':
        LL = m_gain_L * 0.5; LR = m_gain_R * -0.5
        RL = m_gain_L * 0.5; RR = m_gain_R * -0.5

    # off ==> L , R  (regular stereo)
    elif state['midside'] == 'off':
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

    freqs = EQ_CURVES['freqs']
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
            bfeq2png.do_graph(freqs, eq_mag)


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


def brutefir_runs():
    if JCLI.get_ports('brutefir'):
        return True
    else:
        return False


# JACK MANAGEMENT: =====================================================
def jack_connect(p1, p2, mode='connect', wait=1):
    """ Low level tool to connect / disconnect a pair of ports,
        by retriyng for a while
    """
    # Will retry during <wait> seconds, this is useful when a
    # jack port exists but it is still not active,
    # for instance Brutefir ports takes some seconds to be active.

    # will retry every second
    while wait:
        try:
            if 'dis' in mode or 'off' in mode:
                JCLI.disconnect(p1, p2)
            else:
                JCLI.connect(p1, p2)
            break
        except jack.JackError as e:
            print( f'(core.jack_connect) Exception: {e}' )
        wait -= 1
        sleep(1)

    if wait:
        return True
    else:
        return False


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
    if not cap_ports:
        print( f'(core) cannot find jack port "{cap_pattern}"' )
        return
    if not pbk_ports:
        print( f'(core) cannot find jack port "{pbk_pattern}"' )
        return

    mode = 'disconnect' if ('dis' in mode or 'off' in mode) else 'connect'
    for cap_port, pbk_port in zip(cap_ports, pbk_ports):
        job_jc = threading.Thread( target=jack_connect,
                                   args=(cap_port, pbk_port, mode, wait) )
        job_jc.start()


def jack_clear_preamp():
    """ Force clearing ANY clients, no matter what input was selected
    """
    preamp_ports = JCLI.get_ports('pre_in_loop', is_input=True)
    for preamp_port in preamp_ports:
        for client in JCLI.get_all_connections(preamp_port):
            jack_connect( client, preamp_port, mode='off' )


# THE PREAMP: AUDIO PROCESSOR, SELECTOR, and SYSTEM STATE KEEPER =======
def init_source():
    """ Forcing if indicated on config.yml or restoring last state from disk
    """
    preamp = Preamp()

    if CONFIG["on_init"]["input"]:
        preamp.select_source  (   CONFIG["on_init"]["input"]      )
    else:
        preamp.select_source  (   preamp.state['input']             )

    preamp.save_state()
    del(preamp)


def init_audio_settings():
    """ Forcing if indicated on config.yml or restoring last state from disk
    """

    preamp    = Preamp()
    convolver = Convolver()

    # (i) using is not None below to detect 0 or False values

    on_init = CONFIG["on_init"]

    if on_init["muted"] is not None:
        preamp.set_mute       (   on_init["muted"]                )
    else:
        preamp.set_mute       (   preamp.state['muted']           )

    if on_init["level"] is not None:
        preamp.set_level      (   on_init["level"]                )
    else:
        preamp.set_level      (   preamp.state['level']           )

    if on_init["max_level"] is not None:
        preamp.set_level(  min( on_init["max_level"],
                                preamp.state['level'] ) )

    if on_init["bass"] is not None :
        preamp.set_bass       (   on_init["bass"]                 )
    else:
        preamp.set_bass       (   preamp.state['bass']            )

    if on_init["treble"] is not None :
        preamp.set_treble     (   on_init["treble"]               )
    else:
        preamp.set_treble     (   preamp.state['treble']          )

    if on_init["balance"] is not None :
        preamp.set_balance    (   on_init["balance"]              )
    else:
        preamp.set_balance    (   preamp.state['balance']         )

    if on_init["loudness_track"] is not None:
        preamp.set_loud_track (   on_init["loudness_track"]       )
    else:
        preamp.set_loud_track (   preamp.state['loudness_track']  )

    if on_init["loudness_ref"] is not None :
        preamp.set_loud_ref   (   on_init["loudness_ref"]         )
    else:
        preamp.set_loud_ref   (   preamp.state['loudness_ref']    )

    if on_init["midside"]:
        preamp.set_midside    (   on_init["midside"]              )
    else:
        preamp.set_midside    (   preamp.state['midside']         )

    if on_init["solo"]:
        preamp.set_solo       (   on_init["solo"]                 )
    else:
        preamp.set_solo       (   preamp.state['solo']            )

    if on_init["xo"]:
        convolver.set_xo      (   on_init["xo"]                   )
        preamp.state["xo_set"] = on_init["xo"]
    else:
        convolver.set_xo      (   preamp.state['xo_set']          )

    if on_init["drc"]:
        convolver.set_drc     (   on_init["drc"]                  )
        preamp.state["drc_set"] = on_init["drc"]
    else:
        convolver.set_drc     (   preamp.state['drc_set']         )

    if on_init["target"]:
        preamp.set_target     (   on_init["target"]               )
    else:
        preamp.set_target     (   preamp.state['target']          )

    preamp.save_state()
    del(convolver)
    del(preamp)


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
            set_loud_ref
            set_loud_track
            set_target
            set_solo
            set_mute
            set_midside

            get_state
            get_inputs
            get_target_sets
            get_eq

    """

    def __init__(self):

        # The available inputs
        self.inputs = CONFIG['sources']
        # The state dictionary
        self.state = yaml.safe_load( open(STATE_PATH, 'r') )
        # will add some informative values:
        self.state['loudspeaker'] = CONFIG['loudspeaker']
        self.state['peq_set'] = get_peq_in_use()
        self.state['fs'] = JCLI.samplerate
        # The target curves available under the 'eq' folder
        self.target_sets = find_target_sets()
        # The available span for tone curves
        self.bass_span   = int( (EQ_CURVES['bass_mag'].shape[1] - 1) / 2 )
        self.treble_span = int( (EQ_CURVES['treb_mag'].shape[1] - 1) / 2 )
        # Max authorised gain
        self.gain_max    = float(CONFIG['gain_max'])
        # Max authorised balance
        self.balance_max = float(CONFIG['balance_max'])

    def _validate( self, candidate ):
        """ Validates that the given 'candidate' (new state dictionary)
            does not exceed gain limits
        """

        gmax            = self.gain_max
        gain            = calc_gain( candidate )
        eq_mag, eq_pha  = calc_eq( candidate )
        bal             = candidate['balance']

        headroom = gmax - gain - np.max(eq_mag) - np.abs(bal / 2.0)

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
        with open(STATE_PATH, 'w') as f:
            yaml.safe_dump( self.state, f, default_flow_style=False )

    # Bellow we use *dummy to accommodate the preamp.py parser mechanism
    # wich always will include two arguments for any function call.

    def get_state(self, *dummy):
        #return yaml.safe_dump( self.state, default_flow_style=False )
        self.state['convolver_runs'] = brutefir_runs()      # informative
        return self.state

    def get_target_sets(self, *dummy):
        return self.target_sets

    def set_level(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate['level'] += round(float(value), 2)
        else:
            candidate['level'] =  round(float(value), 2)
        return self._validate( candidate )

    def set_balance(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate['balance'] += round(float(value), 2)
        else:
            candidate['balance'] =  round(float(value), 2)
        if abs(candidate['balance']) <= self.balance_max:
            return self._validate( candidate )
        else:
            return 'too much'

    def set_bass(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate['bass'] += round(float(value), 2)
        else:
            candidate['bass'] =  round(float(value), 2)
        if abs(candidate['bass']) <= self.bass_span:
            return self._validate( candidate )
        else:
            return 'too much'

    def set_treble(self, value, relative=False):
        candidate = self.state.copy()
        if relative:
            candidate['treble'] += round(float(value), 2)
        else:
            candidate['treble'] =  round(float(value), 2)
        if abs(candidate['treble']) <= self.treble_span:
            return self._validate( candidate )
        else:
            return 'too much'

    def set_loud_ref(self, value, relative=False):
        candidate = self.state.copy()
        # this try if intended just to validate the given value
        try:
            if relative:
                candidate['loudness_ref'] += round(float(value), 2)
            else:
                candidate['loudness_ref'] =  round(float(value), 2)
            return self._validate( candidate )
        except:
            return 'bad value'

    def set_loud_track(self, value, *dummy):
        candidate = self.state.copy()
        if type(value) == bool:
            value = str(value)
        try:
            value = { 'on': True , 'off': False,
                      'true': True, 'false': False,
                      'toggle': {True: False, False: True
                                 }[self.state['loudness_track']]
                     } [ value.lower() ]
            candidate['loudness_track'] = value
            return self._validate( candidate )
        except:
            return 'bad option'

    def set_target(self, value, *dummy):
        candidate = self.state.copy()
        if value in self.target_sets:
            candidate['target'] = value
            return self._validate( candidate )
        else:
            return f'target \'{value}\' not available'

    def set_solo(self, value, *dummy):
        if value.lower() in ('off', 'l', 'r'):
            self.state['solo'] = value.lower()
            bf_set_gains( self.state )
            return 'done'
        else:
            return 'bad option'

    def set_polarity(self, value, *dummy):
        if value in ('+', '-', '++', '--', '+-', '-+'):
            self.state['polarity'] = value.lower()
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
                                                 [ self.state['muted'] ]
                        } [ value.lower() ]
                self.state['muted'] = value
                bf_set_gains( self.state )
                return 'done'
        except:
            return 'bad option'

    def set_midside(self, value, *dummy):
        if value.lower() in ( 'mid', 'side', 'off' ):
            self.state['midside'] = value.lower()
            bf_set_gains( self.state )
        else:
            return 'bad option'
        return 'done'

    def get_eq(self, *dummy):
        freq, mag , pha = bf_read_eq()
        return { 'band': freq.tolist(), 'mag': mag.tolist(),
                                        'pha': pha.tolist() }

    def select_source(self, value, *dummy):
        """ this is the source selector """

        def try_select(source):
            w = '' # warnings

            if source == 'none':
                jack_clear_preamp()
                return 'done'

            if source not in self.inputs:
                # do nothing
                return f'unknown source \'{source}\''

            # clearing 'preamp' connections
            jack_clear_preamp()

            # connecting the new SOURCE to PREAMP input
            jack_connect_bypattern( CONFIG['sources'][source]['capture_port'],
                                    'pre_in' )

            # Trying to set the desired xo and drc for this source
            c = Convolver()
            try:
                xo = CONFIG["sources"][source]['xo']
                if xo and c.set_xo( xo ) == 'done':
                    self.state['xo_set'] = xo
                elif xo:
                    w = f'\'xo:{xo}\' in \'{source}\' is not valid'
            except:
                pass
            try:
                drc = CONFIG["sources"][source]['drc']
                if drc and c.set_drc( drc ) == 'done':
                    self.state['drc_set'] = drc
                elif drc:
                    if w:
                        w += ' '
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

        result = try_select(value)

        if result == 'done':
            self.state['input'] = value
            candidate = self.state.copy()
            candidate = on_change_input_behavior(candidate)
            # Special source loudness_ref overrides
            # the one in on_change_input_behavior
            try:
                candidate["loudness_ref"] = \
                               CONFIG["sources"][value]['loudness_ref']
            except:
                pass
            # Special source target setting overrides the one in on_init
            try:
                candidate["target"] = CONFIG["sources"][value]['target']
            except:
                candidate["target"] = CONFIG["on_init"]['target']
            self._validate( candidate )

        return result

    def get_inputs(self, *dummy):
        return [ x for x in self.inputs.keys() ]


# THE CONVOLVER: DRC and XO Brutefir stages management =================
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
        #print('xo_sets:', self.xo_sets) # debug

        # Ways are the XO filter stages definded inside brutefir_config
        # 'f.WW.C' where WW:fr|lo|mi|hi|sw and C:L|R
        self.ways = get_brutefir_config('ways')
        # print('ways:', self.ways) # debug

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


# JCLI: THE CLIENT INTERFACE TO THE JACK SERVER ========================
# IMPORTANT: this module core.py needs JACK to be running.
try:
    JCLI = jack.Client('tmp', no_start_server=True)
except:
    print( '(core) ERROR cannot commuticate to the JACK SOUND SERVER.' )

# COMMON USE VARIABLES: ================================================
UHOME       = os.path.expanduser("~")
CONFIG_PATH = f'{UHOME}/pe.audio.sys/config.yml'
CONFIG      = yaml.safe_load(open(CONFIG_PATH, 'r'))
LSPK_FOLDER = f'{UHOME}/pe.audio.sys/loudspeakers/{CONFIG["loudspeaker"]}'
STATE_PATH  = f'{UHOME}/pe.audio.sys/.state.yml'
EQ_FOLDER   = f'{UHOME}/pe.audio.sys/share/eq'
EQ_CURVES   = find_eq_curves()
# Aux global to avoid dumping magnitude graph if no changed
last_eq_mag = np.zeros( EQ_CURVES['freqs'].shape[0] )

if not EQ_CURVES:
    print( '(core) ERROR loading EQ_CURVES from share/eq/' )
    sys.exit()

LOUD_FLAT_CURVE_INDEX = find_loudness_flat_curve_index()

if LOUD_FLAT_CURVE_INDEX < 0:
    print( f'(core) MISSING FLAT LOUDNESS CURVE. BYE :-/' )
    sys.exit()
