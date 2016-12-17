# Collection of `KiCAD` Parsers in Python 2

## `kicad_pcb` Parser.

To get the python object model of a `kicad_pcb` file,
```python
    from kicad_parser import KicadPCB
    pcb = KicadPCB(filename)
```

Do whatever you like with it.

To export the model back to kicad_pcb,
```python
    pcb.export(filename)
```

More details can be found inside [code](kicad_pcb.py) document.
