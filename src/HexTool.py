import io
import struct


def seek_align_up(filestream: io.BufferedReader, align: int) -> int | None:
    """pad to align"""
    padSize = filestream.tell() % align
    padding, = struct.unpack(f"{padSize}s", filestream.read(padSize))
    assert all([x == 0 for x in padding]), "padding value should be zero"
    return padding


def printHexView(bytestream: bytearray | bytes, width = 32):
    """print hex bytes similar in hex editor, for debug usage"""
    view = ""
    digit = len(str(len(bytestream)))
    for i, b in enumerate(bytestream):
        sep = ' '
        pref = ''
        if i % width == 0:
            pref = ("{0:0"+str(digit)+"d}").format(i) + ": "
        elif i % width == width - 1:
            sep = '\n'
        elif i % 4 == 4 - 1:
            sep = '|'
        view = view + pref + f"{b:02X}" + sep
    print(view)
    return view
