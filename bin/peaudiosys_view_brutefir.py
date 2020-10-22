#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

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

"""
    A script to read the Brutefir convolver structure on pe.audio.sys

    Four objects are provided:

    .outputsMap:         outputs and its corresponding port in JACK.
    .coeffs:             available coefficients.
    .filters_at_start:   filters and coefficients defined into the brutefir_config file.
    .filters_running:    filters and coefficients in progress.

"""

import sys, os
import subprocess as sp
from socket import socket

UHOME = os.path.expanduser("~")

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


def bfcli(cmd):
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


def read_config():
    """ reads outputsMap, coeffs, filters_at_start
    """
    global outputsMap, coeffs, filters_at_start
    global sampling_rate, filter_length, float_bits, dither, init_delays, maxdelay

    with open(BRUTEFIR_CONFIG_PATH, 'r') as f:
        lineas = f.readlines()

    # Outputs storage
    outputIniciado = False
    outputJackIniciado = False
    outputsTmp= ''

    # Coeff storage
    coeffIndex = -1
    coeffIniciado = False

    # Filters Storage
    filterIndex = -1
    filterIniciado = False

    sampling_rate   = ''
    filter_length   = ''
    float_bits      = ''
    dither          = ''
    delay           = ''
    maxdelay        = '(as needed)'

    # Loops reading lines in brutefir.config (skip lines commented out)
    for linea in [x for x in lineas if (x.strip() and x.strip()[0] != '#') ]:

        if 'sampling_rate' in linea:
            sampling_rate = linea.strip().split(':')[-1].strip()

        if 'filter_length' in linea:
            filter_length = linea.strip().split(':')[-1].strip()

        if 'float_bits' in linea:
            float_bits = linea.strip().split(':')[-1].strip()

        if 'dither' in linea:
            dither = linea.strip().split(':')[-1].strip()

        if linea.strip().split()[0] == 'delay:':
            init_delays = linea.strip().split(':')[-1].strip()

        if linea.strip().split()[0] == 'maxdelay:':
            maxdelay = linea.strip().split()[1].strip()


        #######################
        # OUTPUTs
        #######################
        if linea.strip().startswith('output '):
            outputIniciado = True

        if outputIniciado:
            if 'device:' in linea and '"jack"' in linea:
                outputJackIniciado = True

        if outputJackIniciado:
            tmp = linea.split('ports:')[-1].strip()
            if tmp:
                tmp = [ x.strip() for x in tmp.split(',') if x and not '}' in x]
                for item in tmp:
                    item = item.replace('"','').replace(';','')
                    pmap = ( item.split('/')[::-1] )
                    outputsMap.append( pmap ); tmp = ''
            if "}" in linea: # fin de la lectura de las outputs
                outputJackIniciado = False

        #######################
        # COEFFs
        #######################
        if linea.startswith("coeff"):
            coeffIniciado = True
            coeffIndex +=1
            cName = linea.split('"')[1].split('"')[0]

        if coeffIniciado:
            if "filename:" in linea:
                pcm = linea.split('"')[1].split('"')[0].split("/")[-1]
            if "attenuation:" in linea:
                cAtten = linea.split()[-1].replace(';','').strip()
            if "}" in linea:
                try:
                    coeffs.append( {'index':str(coeffIndex), 'name':cName, 'pcm':pcm, 'atten':cAtten} )
                except:
                    coeffs.append( {'index':str(coeffIndex), 'name':cName, 'pcm':pcm, 'atten':'0.0'} )
                coeffIniciado = False


        #######################################
        # FILTERs
        #######################################
        if linea.startswith("filter "):
            filterIniciado = True
            filterIndex +=1
            fName = linea.split('"')[1].split('"')[0]

        if filterIniciado:
            if "coeff:" in linea:
                cName = linea.split(':')[1].strip().replace('"', '').replace(";","")
            if "to_outputs" in linea:
                fAtten = linea.split("/")[-2]
                fPol = linea.split("/")[-1].replace(";","")
            if "}" in linea:
                filters_at_start.append( {'index':filterIndex, 'name':fName, 'coeff':cName} )
                filterIniciado = False


    with open( f'{UHOME}/.brutefir_defaults', 'r') as f:
        lines = f.read().split('\n')

    for line in lines:

        if not sampling_rate:
            if 'sampling_rate' in line:
                sampling_rate = line.strip().split(':')[-1].strip() \
                                + color.BOLD + ' (DEFAULT)' + color.END

        if not filter_length:
            if 'filter_length' in line:
                filter_length = line.strip().split(':')[-1].strip() \
                                + color.BOLD + ' (DEFAULT)' + color.END

        if not float_bits:
            if 'float_bits' in line:
                float_bits = line.strip().split(':')[-1].strip() \
                                + color.BOLD + ' (DEFAULT)' + color.END


def add_atten_pol(f):

    at = 0.0 # atten total
    pol = 1

    for key in ['from inputs', 'to outputs', 'from filters', 'to filters']:
        tmp = f[key].split()
        # index/atten/multiplier, for instance:
        # 0/0.0    1/inf
        # 3/0.0
        # 4/-9.0/-1
        for item in [ x for x in tmp if '/' in x ]:

            # atten
            a = item.split('/')[1]
            if a != 'inf':
                at += float(a)

            # multiplier (polarity)
            try:
                tmp = item.split('/')[2]
                pol *= (int( tmp ) )
            except:
                pass

    f["atten tot"]  = at
    f["pol"]        = pol

    return f


def get_running_filters():

    filters = []
    f_blank = { 'f_num':    None,
                'f_name':   None,
                }

    # query list of filter in Brutefir
    lines = bfcli('lf').split('\n')

    # scanning filters
    f = {}
    for line in lines:

        if line and ':' in line[ :5]:   # ':' pos can vary

            if f:
                f = add_atten_pol(f)
                filters.append( f )

            f = f_blank.copy()
            f["f_num"]  = line.split(':')[0].strip()
            f["f_name"] = line.split(':')[1].strip().replace('"','')

        if 'coeff set:' in line:
            f["coeff set"] = line.split(':')[1].strip()
        if 'delay blocks:' in line:
            f["delay blocks"] = line.split(':')[1].strip()
        if 'from inputs:' in line:
            f["from inputs"] = line.split(':')[1].strip()
        if 'to outputs:' in line:
            f["to outputs"] = line.split(':')[1].strip()
        if 'from filters:' in line:
            f["from filters"] = line.split(':')[1].strip()
        if 'to filters:' in line:
            f["to filters"] = line.split(':')[1].strip()

    # adding the last
    if f:
        f = add_atten_pol(f)
        filters.append( f )

    return filters


def get_running_delays():

    delays = []
    # query list of filter in Brutefir
    lines = bfcli('lo').split('\n')

    for line in lines:
        if line and line[2].isdigit() and line[3]==':':
            delay = line.split(')')[0].split()[-1]
            if delay.split(':')[-1] == '0':
                delay = delay.split(':')[0]
            delays.append(delay)

    return ','.join(delays)


if __name__ == "__main__" :

    # Read the loudspeaker folder where brutefir has been launched
    try:
        tmp = sp.check_output( 'pwdx $(pgrep -f "brutefir\ brutefir_config")',
                                shell=True ).decode()
        LSPK_FOLDER = tmp.split('\n')[0].split(' ')[-1]
        BRUTEFIR_CONFIG_PATH = f'{LSPK_FOLDER}/brutefir_config'
    except:
        print( 'ERROR reading brutefir process' )
        sys.exit()

    outputsMap          = []
    coeffs              = []
    filters_at_start    = []

    # reading outputsMap, coeffs and filters_at_start
    read_config()

    # reading filters_running
    filters_running = get_running_filters()

    # reading current delays
    curr_delays = get_running_delays()

    print()
    print( f'--- Brutefir process runs:' )
    print( f'{BRUTEFIR_CONFIG_PATH}')
    print()
    print( "--- Outputs map:" )
    for output in outputsMap:
        print( output[0].ljust(10), '-->   ', output[1] )

    print()
    print( f'sampling_rate:    {sampling_rate}')
    print( f'filter_length:    {filter_length}')
    print( f'float_bits:       {float_bits}')
    print( f'output_dither:    {dither}')
    print( f'output_maxdelay:  {maxdelay}')
    print( f'outputs_delays:   {init_delays}   (at init)')
    print( color.BOLD + f'                  {curr_delays};   (CURRENT)' + color.END)

    print()
    print( "--- Coeff available:" )
    print( "                       c# coeff                    cAtten pcm_name" )
    print( "                       -- -----                    ------ --------" )
    for c in coeffs:

        cidx    = c['index'].rjust(2)
        cname   = c['name'].ljust(24)
        catt    = '{:+6.2f}'.format( float(c['atten']) )
        pcm     = c['pcm']
        cline_chunk = cidx + ' ' + cname + ' ' + catt + ' ' + pcm
        print( ' ' * 23 + cline_chunk )

    print()
    print( "--- Filters running: (totAttn sumarizes all atten found in filter)\n" )
    print( "f# filter  totAttn pol c# coeff                    cAtten pcm_name" )
    print( "-- ------  ------- --- -- -----                    ------ --------" )
    for f in filters_running:

        # 'f_num': '8', 'f_name': 'f.sw', 'coeff set': '8',
        # 'delay blocks': '0 (0 samples)',
        # 'from inputs': '', 'to outputs': '7/0.0',
        # 'from filters': '2/3.0 3/3.0', 'to filters': '', 'atten tot': 6.0

        fidx    = f['f_num'].rjust(2)

        fname   = f['f_name'].ljust(8)

        fatt    = '{:+6.2f}'.format( float(f['atten tot']) )
        if float(fatt) < 0:
            fatt = color.BOLD + fatt + color.END

        fpol    = str(f['pol']).rjust(2)
        if f["pol"] < 0:
            fpol = color.BOLD + fpol + color.END

        fline_chunk = fidx + ' ' + fname + ' ' + fatt + '  ' + fpol + ' '

        cset    = f['coeff set'].rjust(2)

        try:
            cname = [ c["name"] for c in coeffs if c['index'] == f['coeff set'] ][0]
        except:
            cname = ''
        cname   = cname.ljust(24)

        # The filter can be set to coeff: -1 (no filter), so no matches with coeffs.
        try:
            catt  = [ c["atten"] for c in coeffs if c['index'] == f['coeff set'] ][0]
            catt    = '{:+6.2f}'.format( float(catt) )
            if float(catt) < 0:
                catt = color.BOLD + catt + color.END
        except:
            catt = ''

        try:
            pcm   = [ c["pcm"] for c in coeffs if c['index'] == f['coeff set'] ][0]
        except:
            pcm = ''

        cline_chunk = cset + ' ' + cname + ' ' + catt + ' ' + pcm

        print( fline_chunk + cline_chunk )


    print()
