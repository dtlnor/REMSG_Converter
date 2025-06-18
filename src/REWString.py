from typing import Final

KEY: Final[list[int]] = [0xCF, 0xCE, 0xFB, 0xF8, 0xEC, 0x0A, 0x33, 0x66, 0x93, 0xA9, 0x1D, 0x93, 0x50, 0x39, 0x5F, 0x09]


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

    rawData = bytearray(rawBytes)
    prev = 0
    for i, cur in enumerate(rawData):
        rawData[i] = cur ^ prev ^ KEY[i & 0xF]
        prev = cur
    return bytes(rawData)


def encrypt(rawBytes: bytes) -> bytes:
    """encrypt msg string part"""

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
            stringDict[start_pointer * 2] = stringPool[start_pointer:i]  # local offset : value without \x00
            start_pointer = i + 1  # update sp
    # print(stringDict)
    return stringDict


def wcharPool2StrPool(wcharPool: bytes) -> str:
    """convert utf-16-le bytes to string"""
    assert len(wcharPool) % 2 == 0, "wchar pool should have even size"
    stringPool = wcharPool.decode("utf-16-le")  # each char takes 2 bytes
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
    return (string + "\x00").encode("utf-16-le")


# def StrDict2wcharPool(stringDict: dict[int, str]) -> bytes:
#     return b''.join([toWcharBytes(s) for s in stringDict.values()])

_DEFAULT_IGNORABLE_SET = frozenset(
    {
        0x06DD,
        0x070F,
        0x180E,
        0xFEFF,
        0xE0000,
        0xE0001,
        *range(0x0000, 0x0009),  # 0x0000-0x0008
        *range(0x000E, 0x0020),  # 0x000E-0x001F
        *range(0x007F, 0x0085),  # 0x007F-0x0084
        *range(0x0086, 0x00A0),  # 0x0086-0x009F
        *range(0x180B, 0x180E),  # 0x180B-0x180D
        *range(0x200C, 0x2010),  # 0x200C-0x200F
        *range(0x202A, 0x202F),  # 0x202A-0x202E
        *range(0x2060, 0x2064),  # 0x2060-0x2063
        *range(0x2064, 0x206A),  # 0x2064-0x2069
        *range(0x206A, 0x2070),  # 0x206A-0x206F
        *range(0xD800, 0xE000),  # 0xD800-0xDFFF
        *range(0xFE00, 0xFE10),  # 0xFE00-0xFE0F
        *range(0xFFF0, 0xFFF9),  # 0xFFF0-0xFFF8
        *range(0xFFF9, 0xFFFC),  # 0xFFF9-0xFFFB
        *range(0x1D173, 0x1D17B),  # 0x1D173-0x1D17A
        *range(0xE0002, 0xE0020),  # 0xE0002-0xE001F
        *range(0xE0020, 0xE0080),  # 0xE0020-0xE007F
        *range(0xE0080, 0xE1000),  # 0xE0080-0xE0FFF
    }
)


def isCharDI(char: str) -> bool:
    """Check if character is Default Ignorable Code Point according to Unicode standard"""
    return ord(char) in _DEFAULT_IGNORABLE_SET


def isDI(text: str) -> bool:
    """Check if string has Default Ignorable Code Point according to Unicode standard"""
    if len(text) == 0:
        return False
    return any(isCharDI(char) for char in text)


def escapeDI(text: str) -> str:
    """Escape Default Ignorable Code Points to Unicode escape sequences"""
    result = []
    for char in text:
        if isCharDI(char):
            result.append(f"\\u{ord(char):04x}")
        else:
            result.append(char)
    return "".join(result)
