#!/usr/bin/env python3

# Copyright (c) 2021 Rafael Sánchez
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

import  os
import  sys
from    subprocess  import Popen
from    time        import sleep
from    numpy       import zeros as np_zeros
from    socket      import socket

UHOME = os.path.expanduser("~")
sys.path.append(f'{UHOME}/pe.audio.sys')

from share.jack_mod import  *
from share.miscel   import  CONFIG, LSPK_FOLDER, EQ_CURVES, \
                            BFCFG_PATH, BFDEF_PATH, \
                            get_bf_samplerate, calc_gain, Fmt

if CONFIG["web_config"]["show_graphs"]:
    sys.path.append ( os.path.dirname(__file__) )
    import brutefir_eq2png


# Global to avoid dumping EQ magnitude png graph if not changed
last_eq_mag = np_zeros( EQ_CURVES["freqs"].shape[0] )


def bf_cli(cmd):
    """ A socket client that queries commands to Brutefir
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
        also will dump an EQ graph png file
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
            brutefir_eq2png.do_graph( freqs, eq_mag,
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


def bf_get_configured(prop):
    """ BETA

        Returns a property from Brutefir configuration.

        (i) Currently only works for getting the 'ways' of the loudspeaker)
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


def bf_is_running():
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


def bf_restart_and_reconnect(bf_sources=[]):
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
    # (this can take a while in some machines as Raspberry Pi)
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
    else:
        print(  f'{Fmt.BLUE}(core) Brutefir ports are alive.{Fmt.END}')

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


def bf_get_config_outputs():
    """ Read outputs from 'brutefir_config' file, then gets a dictionary.
    """
    outputs = {}

    with open(BFCFG_PATH, 'r') as f:
        bfconfig = f.read().split('\n')

    output_section = False

    for line in bfconfig:

        line = line.split('#')[0]
        if not line:
            continue

        if   line.strip().startswith('logic') or \
             line.strip().startswith('coeff') or \
             line.strip().startswith('input') or \
             line.strip().startswith('filter'):
                output_section = False
        elif line.strip().startswith('output'):
                output_section = True

        if not output_section:
            continue

        line = line.strip()

        if line.startswith('output') and '{' in line:
            output_section = True
            if output_section:
                outs = line.replace('output', '').replace('{', '').split(',')
                outs = [ x.replace('"', '').strip() for x in outs ]

        if line.startswith('delay:'):
            i = 0
            delays = line.replace('delay:', '').split(';')[0].strip().split(',')
            delays = [ int(x.strip()) for x in delays ]
            for oname, delay in zip(outs, delays):
                outputs[str(i)] = {'name': oname, 'delay': delay}
                i += 1

        if line.startswith('maxdelay:'):
            maxdelay = int( line.split(':')[1].replace(';', '').strip() )
            outputs['maxdelay'] = maxdelay

    return outputs


def bf_get_current_outputs():
    """ Read outputs from running Brutefir, then gets a dictionary.
    """

    lines = bf_cli('lo').split('\n')
    outputs = {}

    i = lines.index('> Output channels:') + 1

    while True:

        onum = lines[i].split(':')[0].strip()

        outputs[str(onum)] = {
            'name':  lines[i].split(':')[1].strip().split()[0].replace('"', ''),
            'delay': int(lines[i].split()[-1].strip().replace(')', '').split(':')[0])
        }

        i += 1
        if not lines[i] or lines[i] == '':
            break

    # Adding maxdelay info from config_file, because not available on runtime
    outputs['maxdelay'] = bf_get_config_outputs()['maxdelay']

    return outputs


def bf_add_delay(ms):
    """ Will add a delay to all outputs, relative to the  delay values
        as configured under 'brutefir_config'.
        Useful for multiroom simultaneous listening.
    """

    result  = 'nothing done'

    outputs = bf_get_config_outputs()
    FS      = int( get_bf_samplerate() )

    # From ms to samples
    delay = int( FS  * ms / 1e3)

    cmd = ''
    too_much = False
    max_available    = outputs['maxdelay']
    max_available_ms = max_available / FS * 1e3

    for o in outputs:

        # Skip non output number item (i.e. the  maxdelay item)
        if not o.isdigit():
            continue

        cfg_delay = outputs[o]['delay']
        new_delay = int(cfg_delay + delay)
        if new_delay > outputs['maxdelay']:
            too_much = True
            max_available    = outputs['maxdelay'] - cfg_delay
            max_available_ms = max_available / FS * 1e3
        cmd += f'cod {o} {new_delay};'

    # Issue new delay to Brutefir's outputs
    if not too_much:
        #print(cmd) # debug
        result = bf_cli( cmd ).lower()
        #print(result) # debug
        if not 'unknown command' in result and \
           not 'out of range' in result and \
           not 'invalid' in result and \
           not 'error' in result:
                result = 'done'
        else:
                result = 'Brutefir error'
    else:
        print(f'(i) ERROR Brutefir\'s maxdelay is {int(max_available_ms)} ms')
        result = f'max delay {int(max_available_ms)} ms exceeded'

    return result