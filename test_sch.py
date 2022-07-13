#!/usr/bin/env python

from kicad_sch import *
from sexp_parser import *

import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filename", nargs='?', default='test.kicad_sch', help='If not used, the default is test.kicad_sch')
parser.add_argument("-l", "--log", dest="logLevel",
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    help="Set the logging level")
parser.add_argument("-o", "--output", help="output filename")
args = parser.parse_args()
logging.basicConfig(level=args.logLevel,
        format="%(filename)s:%(lineno)s: %(levelname)s - %(message)s")

sch = KicadSCH.load(args.filename)

# check for error
for e in sch.getError():
    print('Error: {}'.format(e))

print('root values: ')
for k in sch:
    print('\t{}: {}'.format(k, sch[k]))

print('\nversion: {}'.format(sch.version))

# KicadSCH will ensure several common keys to be presented even if there is none,
# in which case an empty SexpList will be inserted. And if there is only one instance,
# it will be converted to SexpList with one instance two. This is to spare the pain to
# always check key presence and to check whether it is a list
#
# However, KicadSCH does not exhaust all the possibilities, you insert your own keys into
# kicad_sch.py. Or, do as follow
print('\naccess using SexpList')
if 'general' in sch:
    for k in SexpList(sch.general):
        print(k)

if args.output:
    sch.export(sys.stdout if args.output=='-' else args.output)
