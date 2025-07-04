#!/usr/bin/env python3

"""
A simple tool to wire only Brutefir outputs by a given pattern.

usage:   solo.py  <option>

    save        dump to disk the current Brutefir --> system connections
    all         restore Brutefir connectios as per disk info
    pattern     connect only Brutefir ports by the given <pattern>
"""

import sys
import subprocess as sp
import json

THIS_DIR    = __file__[ :__file__.rfind('/')]
CONNS_PATH  = f'{THIS_DIR}/.solo_saved'


def get_brutefir_system():

    tmp = sp.check_output('jack_lsp -c brutefir'.split()).decode().strip()

    tmp = tmp.replace('\n   ', '   ').split('\n')

    resu = [ x.split() for x in tmp if 'system:' in x ]

    return resu


def save():

    with open(CONNS_PATH, 'w') as f:
        f.write( json.dumps( get_brutefir_system() ) )

    for c in get_saved():
        print(c)

    print(f'--> SAVED TO {CONNS_PATH}')


def get_saved():

    try:
        with open(CONNS_PATH, 'r') as f:
            res = json.loads( f.read() )
    except Exception as e:
        res = []

    return res


def do_solo(what):

    for c in conns:

        with open('/dev/null', 'w') as devnull:

            if what in c[0]:
                cmd = 'jack_connect'
            else:
                cmd = 'jack_disconnect'

            sp.Popen(f'{cmd} {c[0]} {c[1]}'.split(), stdout=devnull, stderr=devnull)


def do_all():

    for c in conns:

        with open('/dev/null', 'w') as devnull:
            cmd = 'jack_connect'
            sp.Popen(f'{cmd} {c[0]} {c[1]}'.split(), stdout=devnull, stderr=devnull)


if __name__ == '__main__':

    conns = get_saved()

    if not conns:
        print('You may want to save the current connections first of all.')

    if sys.argv[1:]:

        opc = sys.argv[1]

        if opc == 'all':
            do_all()

        elif opc == 'save':
            save()

        elif '-h' in opc:
            print(__doc__)
            sys.exit()

        else:
            do_solo(opc)

    else:
        print(__doc__)
        sys.exit()
