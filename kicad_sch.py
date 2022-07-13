'''

``kicad_sch`` parser using `sexp_parser.SexpParser`

The parser `KicadSCH` demonstrates the usage of a more general S-expression
parser of class `sexp_parser.SexpParser`. Check out the source to see how easy
it is to implement a parser in an almost declarative way.

A usage demonstration is available in `test_sch.py`
'''

try:
    from .sexp_parser import *
except ImportError:
    from sexp_parser.sexp_parser import *

__author__ = "Heck, Leandro"
__copyright__ = "Copyright 2022, Leandro Heck"
__license__ = "MIT"
__version__ = "1.0.0"
__email__ = "leoheck@gmail.com"
__status__ = "Prototype"


class KicadSCH_gr_text(SexpParser):
    __slots__ = ()
    _default_bools = 'hide'


class KicadSCH_drill(SexpParser):
    __slots__ = ()
    _default_bools = 'oval'


class KicadSCH_pad(SexpParser):
    __slots__ = ()
    _parse1_drill = KicadSCH_drill

    def _parse1_layers(self,data):
        if not isinstance(data,list) or len(data)<3:
            raise ValueError('expects list of more than 2 element')
        return Sexp(data[1],data[2:],data[0])


class KicadSCH_symbol(SexpParser):
    __slots__ = ()
    _default_bools = 'locked'
    _parse_fp_text = KicadSCH_gr_text
    _parse_pad = KicadSCH_pad


class KicadSCH(SexpParser):

    # To make sure the following key exists, and is of type SexpList

    _symbol = [
        'lib_id',
        'in_bom',
        'on_board',
        'uuid',
        'property',
        'pin'
        ]

    _sheet_instances = [
        'path',
        ]

    _defaults = (
        'uuid',
        'paper',
        'title_block',
        'lib_symbols',
        'junction',
        'wire',
        'text',
        'label'
        'symbol',
        'sheet_instances',
        'symbol_instances'
        )


    # _defaults = ('net',
    #             ('net_class','add_net'),
    #             'dimension',
    #             'gr_text',
    #             'gr_line',
    #             'gr_circle',
    #             'gr_arc',
    #             'gr_curve',
    #             'segment',
    #             'arc',
    #             'via',
    #             ['module'] + _footprint,
    #             ['footprint'] + _footprint,
    #             ('zone', 'filled_polygon'))

    _parse_symbol = KicadSCH_symbol
    _parse_symbol = KicadSCH_symbol
    _parse_gr_text = KicadSCH_gr_text

    def export(self, out, indent='  '):
        exportSexp(self, out,'', indent)

    def getError(self):
        return getSexpError(self)

    @staticmethod
    def load(filename, quote_no_parse=None):
        with open(filename, 'r') as f:
            return KicadSCH(parseSexp(f.read(), quote_no_parse))
