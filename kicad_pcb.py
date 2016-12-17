#!/usr/bin/env python
'''
``kicad_pcb`` parser written in Python 2

To get the python object model of a ``kicad_pcb`` file ::
    
    from kicad_parser import KicadPCB
    pcb = KicadPCB(filename)

Do whatever you like with it.

To export the model back to kicad_pcb ::

    pcb.export(filename)

The parser `KicadPCB` demostrates the usage of a more gernal S-expression parser
of class `SexpParser`. Check out the source to see how easy it is to implement a
parser in an almost declarative way.

The `KicadPCB` parser class does not implement a complete kicad_pcb parser, in
the sense that some of the expressions are stored in raw list-based format (i.e.
those parses implemented by class `SexpParserRaw`). In fact, not all expressions
are specified in KiCAD's own document for kicad_pcb `format
<http://kicad-pcb.org/help/file-formats/>`_.  The user can either access the raw
``list`` directly, or implement sub parser on their own (See class
`SexpParser`). Either way, if done right, `KicadPCB` cand still export the
modified model back to kicad_pcb file.

The object model is organized by the following rules

* The ``<value>`` of an S-express ``(<key>, <value>)`` is stored in
  ``<object>.<key>``, where ``<object>`` holds the value of the parent key, and
  the root being an object of class `KicadDPCB`

* If multiple expressions with the same key is expected at the same level, then
  the corresponding ``<key>`` attribute will be a ``list`` of objects holding
  the value.

* None-parsed raw data is stored into ``<object>._raw`` with each expression
  being a ``list`` of the form ::

        [ <line number>, <key>, [ <value> ] ]
    
* A few exceptions,

    * Root level ``(net <id> <name>)`` is stored as an ordered dictionary
      ``KicadPCB.net`` with ``<id>`` as key, ``<name>`` as value,

    * Root level ``(layers (<id>,<name>,<attr>)...)`` is stored as an ordered
      dictionary ``KicadPCB.layers`` with ``<name>`` as key, and class
      `KicadPCB_layer` as value holding ``id`` and ``attr`` attributes.

* Strings inside kicad_pcb file are copied as they are with optional quotes
  untouched for easy export. However, it means that you need to be careful if 
  you want to export after modifying unquoted string.
'''

from sexp_parser import *
from collections import OrderedDict

__author__ = "Zheng, Lei"
__copyright__ = "Copyright 2016, Zheng, Lei"
__license__ = "MIT"
__version__ = "1.0.0"
__email__ = "realthunder.dev@gmail.com"
__status__ = "Prototype"


class KicadPCB_layer(object):
    __slots__ = 'id','attr'
    def __init__(self,value):
        if len(value)!=3:
            raise ValueError('len={}->3'.format(len(value)))
        self.id = int(value[0])
        self.attr = value[2]


class KicadPCB_font(SexpParser):
    __slots__ = 'size','thickness'
    _parse1_size = parseFloat2
    _parse1_thickness = parseFloat1


class KicadPCB_effects(SexpParser):
    __slots__ = 'font','justify'
    _parse1_font = KicadPCB_font
    _parse1_justify = parseCopy1


def parseAt(obj,value):
    '''Handles kicad_pcb (at...) expression.
        
        kicad (at...) may contain 2 entries for x,y or 3 entries for 
        the additional angle(orientation) information
    '''
    if len(value)<2 or len(value)>3:
        raise ValueError('len error')
    return [float(v) for v in value]


class KicadPCB_gr_text(SexpParser):
    __slots__ = 'text','at','layer','effects','hide'
    def __init__(self,value):
        self.text = value[0]
        super(KicadPCB_gr_text,self).__init__(value[1:])

    _parse1_at = parseAt
    _parse1_layer = parseCopy1
    _parse1_effects = KicadPCB_effects
    _parse1_hide = parseEmpty

    _export_text = exportValueOnly
    _export_hide = exportKeyOnly
        

class KicadPCB_gr_line(SexpParser):
    __slots__ = 'start','end','width','layer'
    _parse1_start = parseFloat2
    _parse1_end = parseFloat2
    _parse1_width = parseFloat1
    _parse1_layer = parseCopy1


class KicadPCB_gr_arc(SexpParser):
    __slots__ = 'angle','start','end','width','layer'
    _parse1_angle = parseFloat1
    _parse1_start = parseFloat2
    _parse1_end = parseFloat2
    _parse1_width = parseFloat1
    _parse1_layer = parseCopy1


class KicadPCB_gr_circle(SexpParser):
    __slots__ = 'center','end','width','layer'
    _parse1_center = parseFloat2
    _parse1_end = parseFloat2
    _parse1_width = parseFloat1
    _parse1_layer = parseCopy1


class KicadPCB_segment(SexpParser):
    __slots__ = 'start','end','width','layer','net'
    _parse1_start = parseFloat2
    _parse1_end = parseFloat2
    _parse1_width = parseFloat1
    _parse1_layer = parseCopy1
    _parse1_net = parseInt1


class KicadPCB_via(SexpParser):
    __slots__ = 'at','size','drill','layers','net'
    _parse1_at = parseFloat2
    _parse1_size = parseFloat1
    _parse1_drill = parseFloat1
    _parse1_layers = parseCopy
    _parse1_net = parseInt1


class KicadPCB_pts(SexpParser):
    __slots__ = 'xy'
    _parse_xy = parseFloat2


class KicadPCB_polygon(SexpParser):
    __slots__ = 'pts'
    _parse1_pts = KicadPCB_pts


class KicadPCB_zone(SexpParser):
    __slots__ = 'priority','net','net_name','layer','tstamp','hatch',\
            'connect_pads','min_thickness','fill','polygon','filled_polygon'
    _parse1_priority = parseInt1
    _parse1_net = parseInt1
    _parse1_net_name = parseCopy1
    _parse1_layer = parseCopy1
    _parse1_tstamp = parseCopy1
    _parse1_hatch = parseCopy
    _parse1_connect_pads = SexpParserRaw
    _parse1_min_thickness = parseFloat1
    _parse1_fill = SexpParserRaw
    _parse1_polygon = KicadPCB_polygon
    _parse_filled_polygon = KicadPCB_polygon


class KicadPCB_fp_text(KicadPCB_gr_text):
    __slots__ = ('type',) + KicadPCB_gr_text.__slots__
    def __init__(self,value):
        self.type = value[0]
        super(KicadPCB_fp_text,self).__init__(value[1:])

    _export_type = exportValueOnly


class KicadPCB_xyz(SexpParser):
    __slots__ = 'xyz'
    _parse1_xyz = parseFloat3


class KicadPCB_model(SexpParser):
    __slots__ = 'filename','at','scale','rotate'

    def __init__(self,value):
        self.filename = value[0]
        super(KicadPCB_model,self).__init__(value[1:])

    _parse1_at = KicadPCB_xyz
    _parse1_scale = KicadPCB_xyz
    _parse1_rotate = KicadPCB_xyz

    _export_filename = exportValueOnly


class KicadPCB_pad(SexpParser):
    __slots__ = 'number','type','shape','at','size','drill','layers','net',\
            'solder_paste_margin_ratio'
    def __init__(self,value):
        self.number = value[0]
        self.type = value[1]
        self.shape = value[2]
        super(KicadPCB_pad,self).__init__(value[3:])

    _parse1_at = parseAt
    _parse1_size = parseFloat2
    _parse1_layers = parseCopy
    _parse1_net = parseCopy
    _parse1_solder_paste_margin_ratio = parseFloat1

    def _parse1_drill(self,value):
        if len(value)==3:
            if value[0]!='oval':
                raise ValueError('unknown drill')
            return [float(value[1]),float(value[2])]
        if len(value)!=1:
            raise ValueError('len={}->{}'.format(len(value),1))
        return float(value[0])

    def _export_drill(self,out,key,value,prefix,indent):
        out.write('\n{}({}'.format(prefix,key))
        if isinstance(value,list):
            out.write(' oval {} {})'.format(value[0],value[1]))
        else:
            out.write(' {})'.format(value))

    _export_number = exportValueOnly
    _export_type = exportValueOnly
    _export_shape = exportValueOnly


class KicadPCB_module(SexpParser):
    __slots__ = 'name','locked','layer','tedit','tstamp',\
        'at','descr','tags','path','attr','fp_text',\
        'fp_line','fp_circle','fp_arc','pad','model'
    def __init__(self,value):
        self.name = value[0]
        super(KicadPCB_module,self).__init__(value[1:])

    _parse1_locked = parseEmpty
    _parse1_attr = parseCopy1
    _parse1_layer = parseCopy1
    _parse1_tedit = parseCopy1
    _parse1_tstamp = parseCopy1
    _parse1_at = parseAt
    _parse1_descr = parseCopy1
    _parse1_tags = parseCopy1
    _parse1_path = parseCopy1
    _parse_pad = KicadPCB_pad
    _parse_fp_line = KicadPCB_gr_line
    _parse_fp_arc = KicadPCB_gr_arc
    _parse_fp_circle = KicadPCB_gr_circle
    _parse_fp_text = KicadPCB_fp_text
    _parse_model = KicadPCB_model

    _export_name = exportValueOnly
    _export_locked = exportKeyOnly
    

class KicadPCB(SexpParser):
    __slots__ = 'version','host','general','page','setup','layers',\
            'net','net_class','module','gr_text','gr_line','gr_circle',\
            'gr_arc','segment','via','zone'
        
    def __init__(self,filename):
        data = parseSexp(open(filename, "r").readlines())

        if data is None or len(data)<2 or data[1]!='kicad_pcb':
            raise ValueError('invalid header keywrod {}'.format(data[1]))

        self.net = OrderedDict()
        self.layers = OrderedDict()

        # skip line number (data[0]) and header (data[1]=='kicad_pcb')
        super(KicadPCB,self).__init__(data[2:])

    _parse1_version = parseInt1
    _parse1_host = SexpParserRaw
    _parse1_general = SexpParserRaw
    _parse1_page = SexpParserRaw
    _parse1_setup = SexpParserRaw
    _parse_net_class = SexpParserRaw
    _parse_module = KicadPCB_module
    _parse_gr_text = KicadPCB_gr_text
    _parse_gr_line = KicadPCB_gr_line
    _parse_gr_arc = KicadPCB_gr_arc
    _parse_gr_circle = KicadPCB_gr_circle
    _parse_segment = KicadPCB_segment
    _parse_via = KicadPCB_via
    _parse_zone = KicadPCB_zone

    def _parse_layers(self,value):
        for entry in value:
            if entry[2] in self.layers:
                # layer with duplicate names
                self._err.append(('duplicate',entry))
                logger.error(self._err[-1])
            else:
                self.layers[entry[2]] = KicadPCB_layer(entry[1:])

    def _parse_net(self,value):
        if len(value)!=2:
            raise ValueError('len={}>2'.format(len(value)))
        index = int(value[0])
        if index in self.net:
            raise ValueError('duplicate net')
        self.net[index] = value[1]

    def _export_layers(self,out,key,value,prefix,indent):
        out.write('\n{}({}'.format(prefix,key))
        prefix += indent
        for name, layer in value.iteritems():
            out.write('\n{}({} {} {})'.format(prefix,layer.id,name,layer.attr))
        out.write(')')

    def _export_net(self,out,key,value,prefix,indent):
        for i,name in value.iteritems():
            out.write('\n{}({} {} {})'.format(prefix,key,i,name))

    def export(self, out, indent='  '):
        f = None
        if isinstance(out,basestring):
            out = f = open(out,'w')
        super(KicadPCB,self)._export(out,'kicad_pcb','',indent)
        if f is not None: f.close()


if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename",nargs=1)
    parser.add_argument("-l", "--log", dest="logLevel", 
	choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
	help="Set the logging level")
    parser.add_argument("-o", "--output", help="output filename")
    args = parser.parse_args()    
    logging.basicConfig(level=args.logLevel,
            format="%(filename)s:%(lineno)s: %(levelname)s - %(message)s")
    if args.output:
        KicadPCB(args.filename[0]).export(args.output)
    else:
        KicadPCB(args.filename[0]).export(sys.stdout)
