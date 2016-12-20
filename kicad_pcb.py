'''
``kicad_pcb`` parser using `sexp_parser.SexpParser`

The parser `KicadPCB` demostrates the usage of a more gernal S-expression
parser of class `sexp_parser.SexpParser`. Check out the source to see how easy
it is to implement a parser in an almost declarative way.

A usage demostration is avaiable in `test.py`
'''

from sexp_parser import *

__author__ = "Zheng, Lei"
__copyright__ = "Copyright 2016, Zheng, Lei"
__license__ = "MIT"
__version__ = "1.0.0"
__email__ = "realthunder.dev@gmail.com"
__status__ = "Prototype"


class KicadPCB_gr_text(SexpParser):
    __slots__ = ()
    _default_bools = 'hide'


class KicadPCB_drill(SexpParser):
    __slots__ = ()
    _default_bools = 'oval'


class KicadPCB_pad(SexpParser):
    __slots__ = ()
    _parse1_drill = KicadPCB_drill


class KicadPCB_module(SexpParser):
    __slots__ = ()
    _default_bools = 'locked'
    _parse_fp_text = KicadPCB_gr_text
    

class KicadPCB(SexpParser):

    _parse_module = KicadPCB_module
    _parse_gr_text = KicadPCB_gr_text

    def export(self, out, indent='  '):
        exportSexp(self,out,'',indent)

    def getError(self):
        return getSexpError(self)

    @staticmethod
    def load(filename):
        with open(filename,'r') as f:
            return KicadPCB(parseSexp(f.read()))

