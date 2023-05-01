from typing import Final


def seekString(offset: int, stringDict: dict[int, str]) -> str:
    """seek string from string dict"""
    assert len(stringDict) > 0, "no string pool but seeking string"
    assert offset in stringDict, f"seeking target not at string pool {offset}"
    return stringDict[offset]


# @DeprecationWarning
# def seekStringFromStrPool(offset: int, stringPool: str) -> str:
#     assert offset % 2 == 0, "expect offset in string pool is even"
#     startPos = offset // 2
#     if startPos > 0:
#         assert stringPool[startPos-1] == "\x00", f"string not start from end of previous string when seeking({startPos})"
#     elif startPos < 0:
#         print(startPos)
#         raise IndexError(f"seeking target not at string pool {startPos}")
#     endpos = stringPool.find('\x00', startPos)
#     assert endpos >= 0, f"incorrect string offset when seeking({startPos},{endpos})"
#     return stringPool[startPos:endpos]


def decrypt(rawBytes: bytes) -> bytes:
    """decrypt msg string part"""
    KEY : Final[list[int]] = [
        0xCF, 0xCE, 0xFB, 0xF8, 0xEC, 0x0A, 0x33, 0x66,
        0x93, 0xA9, 0x1D, 0x93, 0x50, 0x39, 0x5F, 0x09]

    rawData = bytearray(rawBytes)
    prev = 0
    for i, cur in enumerate(rawData):
        rawData[i] = cur ^ prev ^ KEY[i & 0xF]
        prev = cur
    return bytes(rawData)


def encrypt(rawBytes: bytes) -> bytes:
    """encrypt msg string part"""
    KEY : Final[list[int]] = [
        0xCF, 0xCE, 0xFB, 0xF8, 0xEC, 0x0A, 0x33, 0x66,
        0x93, 0xA9, 0x1D, 0x93, 0x50, 0x39, 0x5F, 0x09]

    rawData = bytearray(rawBytes)
    prev = 0
    for i, cur in enumerate(rawData):
        rawData[i] = cur ^ prev ^ KEY[i & 0xF]
        prev = rawData[i]
    return bytes(rawData)


def wcharPool2StrDict(wcharPool: bytes) -> dict[int, str]:
    """wcharPool to stringDict with {offset: content}"""
    if len(wcharPool) == 0:
        return dict()
    
    stringPool = wcharPool2StrPool(wcharPool)

    stringDict: dict[int, str] = dict()
    start_pointer = 0
    for i, wchar in enumerate(stringPool):
        if wchar == "\x00":
            stringDict[start_pointer*2] = stringPool[start_pointer:i] # local offset : value without \x00
            start_pointer = i + 1 # update sp
    # print(stringDict)
    return stringDict


def wcharPool2StrPool(wcharPool: bytes) -> str:
    """convert utf-16-le bytes to string"""
    assert len(wcharPool) % 2 == 0, "wchar pool should have even size"
    stringPool = wcharPool.decode("utf-16-le") # each char takes 2 bytes
    assert stringPool[-1] == "\x00", "ending wchar not null"
    return stringPool


def forceWindowsLineBreak(string: str) -> str:
    """Force /r/n for every linebreak"""
    return string.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    

def calcStrPoolOffsets(stringlist: list[str]) -> dict[str, int]:
    """build a offset dict with {string : offset}"""
    newDict = dict()
    sizeCount = 0
    for string in sorted(set(stringlist)):
        # not adding null terminator here, it will done by toWcharBytes()
        newDict[string] = sizeCount
        sizeCount = sizeCount + len(string) * 2 + 2

    return newDict


def toWcharBytes(string: str) -> bytes:
    """convert string to wchar(bytes) in utf-16-le with null terminator"""
    return (string+'\x00').encode('utf-16-le')


# def StrDict2wcharPool(stringDict: dict[int, str]) -> bytes:
#     return b''.join([toWcharBytes(s) for s in stringDict.values()])
