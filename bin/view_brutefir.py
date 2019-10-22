#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'pe.audio.sys', a PC based personal audio system.

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

"""
    A module intended to read the Brutefir convolver

    Four objects are provided:

    .outputsMap:         outputs and its corresponding port in JACK.
    .coeffs:             available coefficients.
    .filters_at_start:   filters and coefficients defined into the brutefir_config file.
    .filters_running:    filters and coefficients in progress.

"""

import sys, os
import subprocess as sp
import socket


def bfcli(cmds=''):
    """ send commands to brutefir CLI and receive its responses
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 3000))

    s.send( f'{cmds};quit\n'.encode() )

    response = b''
    while True:    
        received = s.recv(4096)
        if received:
            response = response + received
        else:
            break
    s.close()
    #print(response) # debug
    return response.decode()


def read_config():
    """ reads outputsMap, coeffs, filters_at_start
    """
    global outputsMap, coeffs, filters_at_start

    f = open(BRUTEFIR_CONFIG_PATH, 'r')
    lineas = f.readlines()

    # Outputs storage
    outputIniciado = False
    outputJackIniciado = False
    outputsTmp= ''
    outputsMap = []

    # Coeff storage
    coeffIndex = -1
    coeffIniciado = False
    coeffs = []

    # Filters Storage
    filterIndex = -1
    filterIniciado = False
    filters_at_start = []

    # Loops reading lines in brutefir.config
    for linea in lineas:

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


def read_running():
    """ Running filters in Brutefir process
    """
    global filters_running
    filters_running = []
    findex = -1

    ###########################################################
    # Get filters running (query 'lf' to Brutefir)
    ###########################################################
    printado = bfcli("lf; quit")

    for linea in printado.split("\n"):
        atten = ''
        pol   = ''
        if ': "' in linea:
            findex += 1
            fname = linea.split('"')[-2]
        if "coeff set:" in linea:
            cset = linea.split(":")[1].split()[0]
        if "to outputs:" in linea:
            # NOTA: Se asume que se sale a una única output.
            #       Podría no ser cierto en configuraciones experimentales que
            #       mezclen vías sobre un mismo canal de la tarjet de sonido
            if linea.strip() != "to outputs:":
                if linea.count('/') == 2:
                    pol   = linea.split('/')[-1].strip()
                    atten = linea.split('/')[-2].strip()
                else:
                    pol   = '1'
                    atten = linea.split('/')[-1].strip()
            # El caso de las etapas eq y drc que no son salidas finales.
            else:
                pol   = '1'
                atten = '0.0'

            filters_running.append( {'index':str(findex), 'fname':fname, 'cset':cset, 'atten':atten, 'pol':pol} )

    #####################################
    # cross relate filter and  coeffs
    #####################################
    # Tenemos los nombres de los filtros con el número de coeficiente cargado en cada filtro,
    # ahora añadiremos el nombre , el pcm y la atenn del coeficiente.
    for frun in filters_running:
        for coeff in coeffs:
            if frun['cset'] == coeff['index']:
                frun['cname']  = coeff['name']
                frun['cpcm']   = coeff['pcm']
                frun['catten'] = coeff['atten']
        # Completamos campos para posibles filtros con coeff: -1;
        # que no habrán sido detectados en el cruce de arriba 'for coeff in coeffs'
        if int(frun['cset']) < 0:
            frun['cset']    = ''
            frun['cname']   = '-1'
            frun['cpcm']    = '-1'
            frun['catten']  = '0.0'

if __name__ == "__main__" :

    HOME = os.path.expanduser("~")
    sys.path.append(HOME + "/bin")

    try:
        tmp = sp.check_output( 'pwdx $(pgrep brutefir)', shell=True ).decode()
        LSPK_FOLDER = tmp.split('\n')[0].split(' ')[-1]
        BRUTEFIR_CONFIG_PATH = f'{LSPK_FOLDER}/brutefir_config'
        print( f'\n--- Brutefir process runs:' )
        print( f'{BRUTEFIR_CONFIG_PATH}')
    except:
        print( 'ERROR reading brutefir process' )
        sys.exit() 

    read_config()

    read_running()

    ################################
    print( "\n--- Outputs map:" )
    ################################
    for output in outputsMap:
        print( output[0].ljust(10), '-->   ', output[1] )

    ################################
    print( "\n--- Coeffs available:\n" )
    ################################
    print( "                             coeff# coeff                coeffAtten pcm_name" )
    print( "                             ------ -----                ---------- --------" )
    for c in coeffs:
        a = '{:+6.2f}'.format( float(c['atten']) )
        print( " "*29 + c['index'].rjust(4) +"   "+ c['name'].ljust(21) + a.ljust(11) + c['pcm'] )

    ################################
    print( "\n--- Filters Running:\n" )
    ################################
    print( "fil# filterName  atten pol   coeff# coeff                coeffAtten pcm_name" )
    print( "---- ----------  ----- ---   ------ -----                ---------- --------" )
    for f in filters_running:
        fa = '{:+6.2f}'.format( float(f['atten']) )
        ca = '{:+6.2f}'.format( float(f['catten']) )
        print( f['index'].rjust(4) +" "+ f['fname'].ljust(11) + fa + f['pol'].rjust(4) + \
              f['cset'].rjust(7) +"   "+ f['cname'].ljust(21) + ca.ljust(11) + f['cpcm'] )

    print()

