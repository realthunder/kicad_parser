#!/usr/bin/env python

from kicad_pcb import *
from sexp_parser import *
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filename",nargs='?')
parser.add_argument("-l", "--log", dest="logLevel", 
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
    help="Set the logging level")
parser.add_argument("-o", "--output", help="output filename")
args = parser.parse_args()    
logging.basicConfig(level=args.logLevel,
        format="%(filename)s:%(lineno)s: %(levelname)s - %(message)s")

pcb = KicadPCB.load('test.kicad_pcb' if args.filename is None else args.filename[0])

# check for error
for e in pcb.getError():
    print('Error: {}'.format(e))


print('root values: ')
for k in pcb:
    print('\t{}: {}'.format(k,pcb[k]))

print('\nversion: {}'.format(pcb.version))

print('\ngeneral.area: {}'.format(pcb.general.area))
for k in pcb.general.area:
    print('\t{}'.format(k))

# The 0 in (layers (0 F.Cu signal)...) is treated as a string key, not integer.
# Integer index is reserved for accessing unamed values. But, you can write a sub
# parser to change that behavior, i.e. to set a key as integer. You need to make
# sure that there is no clash of key with unamed values.
print('\nlayer[0].name: {}'.format(pcb.layers['0'][0]))

# Add a new layer
# For simple S-Expression without sub S-Epressions, simply use Sexpression(<key>,[<value>...])
pcb.layers['100'] = Sexpression('100',['new.layer','test'])
print('\nlayers:'.format(pcb.general.area))
for k in pcb.layers:
    print('\t{}: {}'.format(k,pcb.layers[k]))

# To delete an expression
del pcb.layers['100']

print('\nafter delete :')
for k in pcb.layers:
    print('\t{}: {}'.format(k,pcb.layers[k]))

# For composite S-Expressions, use SexpParser which accepts list-based
# representation of the S-Expression.  Note that SexpParser expects the
# first element of each S-Expression to be the line number
#
# The assignemnt '=' here will not overwrite existing models, but will be
# appended to a SexpList. 
pcb.module[0].model = SexpParser([0,'model','new/model2',
                            [0, 'at', [0, 'xyz', 0, 1, 2]],
                            [0, 'scale', [0, 'xyz', 0,2,3]],
                            [0, 'rotate', [0, 'xyz', 0,3,4]]])

# Or, use parseSexp() to covert S-Expression in plain text to list-based
# representation
pcb.module[0].model = SexpParser(parseSexp(
    '''(model new/model3 
        (at (xyz 1 2 3)) 
        (scale (xyz 3 5 6)) 
        (rotate (xyz 7.0 8.0 9.0)))
    '''))

print('\nmodule[0].models :')
exportSexp(pcb.module[0].model,sys.stdout)

if args.output:
    pcb.export(sys.stdout if args.output=='-' else args.output)
