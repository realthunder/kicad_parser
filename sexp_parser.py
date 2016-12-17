'''
S-Expression parser written in Python 2

This module provides a function `parseSexp()` to convert S-Expression into a
recursive ``list`` representation in the form ::

    [ <line number>, <key>, [ <value> ] ]

The module also provides an abstract class `SexpParser` for Converting the
``list`` representation of S-Expression into python objects

'''

import re
import logging
import traceback
import bisect

__author__ = "Zheng, Lei"
__copyright__ = "Copyright 2016, Zheng, Lei"
__license__ = "MIT"
__version__ = "1.0.0"
__email__ = "realthunder.dev@gmail.com"
__status__ = "Prototype"

logger = logging.getLogger(__name__)

class SexpParser(object):
    """Basic parser class

        The parser excepts input data to be a python ``list`` representation of
        the S-expression, i.e. a recurisve list of form ::

            [ <line number>, <key>, <value> ]

        where the optional ``<value>`` can be another ``list`` of the same
        format.
        
        The ``SexpParser`` uses the constructor to dispatch lower level parsers.
        It also provides a method `_export()` for recrusive S-expresion stream
        output 
    """

    __slots__ = '_err'

    def __init__(self,data):
        """Constructor that dispatches parsing to lower level parsers

            Args: data (list): holds the value to be parsed. It shall contains a
            list of entries, with each entry defined as ::

                [ <line number>, <subkey>, [<subvalue>] ]

            The constructor will dispatch keyword parsing to lower level parsers
            grouped by ``self`` here. User impelements the actual parsing by
            subclassing this class, and implement the sub-parser as callable
            attributes. 

            Parser named as ``'_parse1_' + <key>`` demands that the
            corresponding key must not appear more than once

            Parser named as ``'_parse_' + <key>`` assumes that the parsed result
            to be stored in an attruibte named as ``<key>`` of type ``list`` The
            attribute is created if not existed.

            Lower level parser can bypass result storage by not returning
            anything, and perform its own storage
        """
        self._err = []
        for entry in data:
            try:
                if not isinstance(entry, (list, tuple)):
                    key = entry
                    value = []
                elif(len(entry)<2):
                    self._err.append(('no keyword',entry))
                    logger.error(self._err[-1])
                    continue
                else:
                    key = entry[1]
                    value = entry[2:]

                if logger.isEnabledFor(logging.INFO):
                    logger.info('{}._parse_{} {}'.format(self.__class__.__name__,key,entry))

                parse = getattr(self,'_parse1_'+key,None)
                if parse is not None:
                    if not hasattr(self,key):
                        ret = parse(value)
                        if ret is not None: setattr(self,key,ret)
                    else:
                        self._err.append(('duplicate',entry))
                        logger.error(self._err[-1])
                    continue

                parse = getattr(self,'_parse_'+key,None)
                if parse is None:
                    self._err.append(('no parser',entry))
                    logger.error(self._err[-1])
                else:
                    ret = parse(value)
                    if ret is None: continue

                    v = getattr(self,key,None)
                    if v is None:
                        setattr(self,key,[ret])
                    else:
                        v.append(ret)

            except Exception as e:
                self._err.append((str(e),entry))
                if logger.isEnabledFor(logging.ERROR):
                    logger.error(self._err[-1])
                    traceback.print_exc()

    def _exportEntry(self,out,key,value,prefix,indent):
        '''Write an S-epression to output stream

            Args: out: output stream, only needs to implement
            ``out.write(string)`` key(string): key of this entry value: value of
            this entry prefix(string): prefixing spaces for output formating
            indent(string): incremental prefix for each level

            The method will first try export using ``<value>._export()`` if
            there is one. Otherwise, it simply exports ::

                <prefix>(<key> <value>)

            If ``<value>`` is a ``list``, it will try each
            ``<subvalue>._export()``.  If there is none, then just export using
            ``str(<value>)``.

            Note: the method consider it as an error for a subvalue to be of
            type ``list``, because it doesn't know what ``<key>`` to use for the
            subvalue.  Recursion is achieve by implementing
            ``<subvalue>._export()``
        '''
        p = getattr(value,'_export',None)
        if p is not None:
            p(out,key,prefix,indent)
            return
        if not isinstance(value,list):
            out.write('\n{}({} {})'.format(prefix,key,str(value)))
            return
        out.write('\n{}({}'.format(prefix,key))
        prefix += indent
        for e in value:
            p = getattr(e,'_export',None)
            if p is not None:
                p(out,key,prefix,indent)
                continue
            if isinstance(e,list):
                logger.error((len(prefix)/len(indent),self.__class__.__name__,key,'no export'))
                continue
            out.write(' ' + str(e))
        out.write(')')

    def _export(self, out, key, prefix, indent):
        '''Export ``self`` to an S-epression and write to output stream

            Args: out: output stream, only needs to implement
            ``out.write(string)`` key(string): key of this entry prefix(string):
            prefixing spaces for output formating indent(string): incremental
            prefix for each level

            This function relies on ``self.__slots__`` to discover the list of
            all keys (i.e. acessed using ``self.<key>``) to export. Any
            attribute starts with '_' is ignored. The order of the keys in
            ``__slots__`` determins the order of export. Also note that,
            subclass relying on this method for export must have a complete
            ``__slots__``, i.e. a slots containing every key it wants to export,
            including those already appear in its super class(s). Python allows
            duplicated entry inside ``__slots__``.
            
            For each non-None keys in ``__slots__``, the method  will first try
            ``self._export_<key>()``. If there is none but there is
            ``self._parse_<key>`` instead, meaning that multiple insance of the
            key value pair are stored in a ``list``, it will exapnd the list and
            call `_exportEntry()` on each element. Otherwise, it just call
            `_exportEntry()` straightaway
        '''

        out.write('\n{}({}'.format(prefix,key))
        prefix += indent
        for subkey in (self.__slots__ if isinstance(self.__slots__,tuple) else (self.__slots__,)):
            if subkey.startswith('_'): continue
            value = getattr(self,subkey,None);
            if value is None: continue
            try:
                p = getattr(self,'_export_'+subkey,None)
                if p is not None: 
                    p(out,subkey,value,prefix,indent)
                    continue
                if hasattr(self,'_parse_'+subkey):
                    for v in value:
                        self._exportEntry(out,subkey,v,prefix,indent)
                else:
                    self._exportEntry(out,subkey,value,prefix,indent)
            except Exception as e:
                logger.error((len(prefix)/len(indent),self.__class__.__name__,subkey,str(e)))
                if logger.isEnabledFor(logging.ERROR):
                    traceback.print_exc()
        out.write(')')


class SexpParserRaw(object):
    '''Helper class for storing raw S-expression that do not need to be parsed

        The raw ``list`` represention of the S-expression is sotred in
        ``self._raw``.  When exporting, it will strip the line number
        information 
    '''
    __slots__ = '_raw'

    def __init__(self,value):
        self._raw = value

    def _exportRaw(self, out, key, value, prefix, indent):
        out.write('\n{}({}'.format(prefix,key))
        prefix += indent
        for v in value:
            if isinstance(v,list):
                self._exportRaw(out, v[1], v[2:], prefix,indent)
            else:
                out.write(' '+str(v))
        out.write(')')

    def _export(self, out, key, prefix, indent):
        self._exportRaw(out,key,self._raw,prefix,indent)


######################################################################################
# Parser helper functions

def parseNone(obj,value):
    """Discards the value"""
    pass

def parseCopy(obj,value):
    """Returns the value as it is"""
    return value

def parseCopySingle(obj,value,index=0,checkLen=0):
    """Returns a single element, optionally check the length

        Args:
            obj: just a place holder so that it can be used as
                 a class callable attribute
            value: value to be parsed
            index(int): index of the element to be copied inside ``value``
            checkLen(int): expected number of elements, 0 means no checking
    """
    if checkLen !=0 and len(value)!=checkLen:
        raise ValueError('len={}->{}'.format(len(value),checkLen))
    return value[index]

def parseCopy1(obj,value):
    """Returns a single element, and checkes ``len(value)==1``"""
    return parseCopySingle(obj,value,0,1)

def parseEmpty(obj,value):
    """Returns empty list, and checkes ``len(value)==0``"""
    if len(value):
        raise ValueError('len={}->0'.format(len(value)))
    return []

def parseList(obj,value,fType,checkLen=0):
    """Coverts all value with the given type function

        Args:
            obj: just a place holder so that it can be used as
                 a class callable attribute
            value: value to be parsed
            fType(callable): for converting each element of ``value``
            checkLen(int): expected number of elements, 0 means no checking
    """
    if checkLen!=0 and len(value)!=checkLen:
        raise ValueError('len={}>{}'.format(len(value),checkLen))
    return [fType(d) for d in value]

def parseInt1(obj,value):
    """Returns ``int(value[0])``, and checkes ``len(value)==1``"""
    if len(value)>1:
        raise ValueError('len={}>1'.format(len(value)))
    return int(value[0])

def parseFloat1(obj,value):
    """Returns ``float(value[0])``, and checkes ``len(value)==1``"""
    if len(value)>1:
        raise ValueError('len={}>1'.format(len(value)))
    return float(value[0])

def parseFloat2(obj,value):
    return parseList(obj,value,float,2)

def parseFloat3(obj,value):
    return parseList(obj,value,float,3)

def parseSexp(sexp):
    """Parses S-expressions and return a ``list`` represention
        
        Code borrowed from: http://rosettacode.org/wiki/S-Expressions, with
        the following modifications,

        * Do not parse numbers
        * Do not strip quotes (for easy export back to S-expression)
        * Added line number information for easy debugging
    """

    if not hasattr(parseSexp,'regex'):
        parseSexp.regex = re.compile(
            r'''(?mx)
                    \s*(?:
                    (?P<l>\()|
                    (?P<r>\))|
                    (?P<q>"[^"]*")|
                    (?P<s>[^(^)\s]+)
                )''')

    # Pre-process data to get index position of each line end
    lines = []
    if isinstance(sexp,(list,tuple)):
        count = 0
        for l in sexp:
            count += len(l)
            lines.append(count)
        sexp = ''.join(sexp)

    stack = []
    out = []
    if logger.isEnabledFor(logging.DEBUG):
    	logger.debug("%-6s %-14s %-44s %-s" % tuple("term value out stack".split()))
    for termtypes in re.finditer(parseSexp.regex, sexp):
        term, value = [(t,v) for t,v in termtypes.groupdict().items() if v][0]
    	if logger.isEnabledFor(logging.DEBUG):
	    logging.debug("%-7s %-14s %-44r %-r" % (term, value, out, stack))
        if   term == 'l': # left bracket
            stack.append(out)
            out = []
        elif term == 'r': # right bracket
            assert stack, "Trouble with nesting of brackets"
            tmpout, out = out, stack.pop(-1)
            out.append(tmpout)
        else:
            if not out: 
                # insert line number as the first element
                out.append(bisect.bisect_right(lines,termtypes.start()))
            if term == 'q': # quoted string
                # out.append(value[1:-1]) # strip quotes
                out.append(value) # do not strip quotes
            elif term == 's': # simple string
                out.append(value)
            else:
                raise NotImplementedError("Error: %r" % (term, value))

    assert not stack, "Trouble with nesting of brackets"

    if not out: return []
    return out[0]

#################################################################################
# export helpers

def exportNone(obj,out,key,value,prefix,indent):
    pass

def exportKeyOnly(obj,out,key,value,prefix,indent):
    out.write(' {}'.format(key))

def exportValueOnly(obj,out,key,value,prefix,indent):
    out.write(' {}'.format(value))


