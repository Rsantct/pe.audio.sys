#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pe.audio.sys'
# 'pe.audio.sys', a PC based personal audio system.
"""
    A simple tool to monitor pe.audio.sys LEVEL filter stages in Brutefir

    'mono' is implemented by cross-mixing the inputs:

                              f.lev.L
                in.L  --------  LL
                       \  ____  LR
                        \/
                        /\____
                       /        RL
                in.R  --------  RR
                              f.lev.R


    A printout example when -3 dB Left balanced and Right in reversed polarity:

                      in L:      in R:
          out L:     30.0 (+)    inf (+)
          out R:      inf (+)   33.0 (-)

"""

from socket import socket
from time import sleep
from subprocess import call


def cli(cmd):
    """ A socket client that queries commands to Brutefir
    """
    # using 'with' will disconnect the socket when done
    ans = ''
    with socket() as s:
        try:
            s.settimeout(1)
            s.connect( ('localhost', 3000) )
            s.send( f'{cmd}; quit;\n'.encode() )
            while True:
                tmp = s.recv(1024)
                if not tmp:
                    break
                ans += tmp.decode()
            s.close()
        except:
            print( f'(brutefir_mod) error: unable to connect to Brutefir:3000' )
    return ans


def main():
    # Excample of filters printout from Brutefir CLI (left ch inverted)
    #  0: "f.lev.L"
    #      coeff set: -1 (no filter)
    #      delay blocks: 0 (0 samples)
    #      from inputs:  0/37.5/-1 1/inf
    #      to outputs:
    #      from filters:
    #      to filters:   2
    #  1: "f.lev.R"
    #      coeff set: -1 (no filter)
    #      delay blocks: 0 (0 samples)
    #      from inputs:  0/inf 1/37.5
    #      ...
    #      ...

    tmp = cli('lf').split('Filters:\n')[-1].split('\n')

    if not tmp[0]:
        print('Cannot connect to Brutefir CLI')
        return False

    tmp = [x for x in tmp if x]

    niveles = []

    empezado = False

    for line in tmp:

        if line[6:12] == 'f.lev.':
            empezado = True

        if 'from inputs' in line and empezado:
            #print(line)
            mix = line.split(':')[-1].strip().split()
            mix = [x.split('/')[1:] for x in mix]
            for x in mix:
                # Bf CLI only prints 3 fields when inverted
                if not x[1:]:
                    x.append('+')
                else:
                    x[1] = '-'

            niveles.append(mix)

        if 'to filters' in line:
            empezado = False

    LL_att =  niveles[0][0][0];    LR_att =  niveles[0][1][0]
    RL_att =  niveles[1][0][0];    RR_att =  niveles[1][1][0]
    LL_pol =  niveles[0][0][1];    LR_pol =  niveles[0][1][1]
    RL_pol =  niveles[1][0][1];    RR_pol =  niveles[1][1][1]

    print('      ',  '  in L:      in R:')
    print('out L:', f'{LL_att.rjust(5)} ({LL_pol})  {LR_att.rjust(5)} ({LR_pol})')
    print('out R:', f'{RL_att.rjust(5)} ({RL_pol})  {RR_att.rjust(5)} ({RR_pol})')
    return True


if __name__ == "__main__":

    # clear terminal
    call('clear')

    while True:
        main()
        sleep(1)
        call('clear')
