import io
import struct
import uuid
from typing import Final

import mmh3
import REWString as helper
from HexTool import pad_align_up

LANG_LIST: Final[dict[int, str]] = {
    0: "Japanese",
    1: "English",
    2: "French",
    3: "Italian",
    4: "German",
    5: "Spanish",
    6: "Russian",
    7: "Polish",
    8: "Dutch",
    9: "Portuguese",
    10: "PortugueseBr",
    11: "Korean",
    12: "TraditionalChinese",  # only this
    13: "SimplifiedChinese",  # and this
    14: "Finnish",
    15: "Swedish",
    16: "Danish",
    17: "Norwegian",
    18: "Czech",
    19: "Hungarian",
    20: "Slovak",
    21: "Arabic",
    22: "Turkish",
    23: "Bulgarian",
    24: "Greek",
    25: "Romanian",
    26: "Thai",
    27: "Ukrainian",
    28: "Vietnamese",
    29: "Indonesian",
    30: "Fiction",
    31: "Hindi",
    32: "LatinAmericanSpanish",
    33: "Max",
}
"""via.Language, with fixing the name of cht and chs"""

LANG_CODE_LIST: Final[dict[int, str]] = {
    0: "Japanese",
    1: "English",
    2: "French",
    3: "Italian",
    4: "German",
    5: "Spanish",
    6: "Russian",
    7: "Polish",
    8: "Dutch",
    9: "Portuguese",
    10: "PortugueseBr",
    11: "Korean",
    12: "TransitionalChinese",
    13: "SimplelifiedChinese",
    14: "Finnish",
    15: "Swedish",
    16: "Danish",
    17: "Norwegian",
    18: "Czech",
    19: "Hungarian",
    20: "Slovak",
    21: "Arabic",
    22: "Turkish",
    23: "Bulgarian",
    24: "Greek",
    25: "Romanian",
    26: "Thai",
    27: "Ukrainian",
    28: "Vietnamese",
    29: "Indonesian",
    30: "Fiction",
    31: "Hindi",
    32: "LatinAmericanSpanish",
    33: "Max",
}
"""via.Language with MHRSB 13.0.0.1.
god damnit, they spell wrong the language name..."""

MHR_SUPPORTED_LANG: Final[list[int]] = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    10,
    11,
    12,
    13,
    21,
    32,
]
"""For MHRSB 15.0.0"""

VERSION_2_LANG_COUNT: Final[dict[int, int]] = {
    12: 23,
    0x2022033D: 27,
    14: 28,
    15: 30,
    17: 32,
    20: 33,
    0x20220626: 33,  # before 13.0.0, 0x20220626 has 32 lang count
    22: 33,
}
"""lang count in each msg version.
0x20220626 has 32 lang count in early version"""


def isVersionEncrypt(version: int) -> bool:
    """check if dataOffset exist"""
    return version > 12 and version != 0x2022033D


def isVersionEntryByHash(version: int) -> bool:
    """check if Entry haed index by hash"""
    return version > 15 and version != 0x2022033D


class Entry:
    """meat of MSG"""

    def __init__(self, version):
        self.version = version

    def readHead(self, filestream: io.BufferedReader, langCount: int):
        """use when reading file only"""

        # we use bytes_le for guid(cuz c# use and store this way)
        self.guid = uuid.UUID(
            bytes_le=struct.unpack("<16s", filestream.read(16))[0],
        )
        (self.crc,) = struct.unpack("<I", filestream.read(4))
        # actually I don't have a version 16 msg file so idk if 16 use hash or index
        if isVersionEntryByHash(self.version):
            (self.hash,) = struct.unpack("<I", filestream.read(4))
        else:
            (self.index,) = struct.unpack("<I", filestream.read(4))

        # offsets below should only be use when reading msg, and once you get the string they should not be use anymore
        (self.entryNameOffset,) = struct.unpack("<Q", filestream.read(8))
        (self.attributeOffset,) = struct.unpack("<Q", filestream.read(8))
        self.contentOffsetsByLangs: list[int] = list()
        for _ in range(langCount):
            self.contentOffsetsByLangs.append(struct.unpack("<Q", filestream.read(8))[0])

    def writeHead(self, bytestream: bytearray):
        """extend the bytearray by filling entry head"""
        bytestream.extend(struct.pack("<16s", self.guid.bytes_le))
        bytestream.extend(struct.pack("<I", self.crc))
        if isVersionEntryByHash(self.version):
            bytestream.extend(struct.pack("<I", self.hash))
        else:
            bytestream.extend(struct.pack("<I", self.index))
        self.entryNameOffsetPH = len(bytestream)
        bytestream.extend(struct.pack("<q", -1))
        self.attributeOffsetPH = len(bytestream)
        bytestream.extend(struct.pack("<q", -1))
        self.contentOffsetsByLangsPH: list[int] = list()
        for _ in self.langs:
            self.contentOffsetsByLangsPH.append(len(bytestream))
            bytestream.extend(struct.pack("<q", -1))

    def readAttributes(self, filestream: io.BufferedReader, attributeHeaders):
        """read the attributes of this msg"""
        self.attributes = list()
        for header in attributeHeaders:
            value = ""
            match header["valueType"]:
                case -1:  # null wstring
                    (value,) = struct.unpack("<Q", filestream.read(8))
                case 0:  # int64
                    (value,) = struct.unpack("<q", filestream.read(8))
                case 1:  # double
                    (value,) = struct.unpack("<d", filestream.read(8))
                case 2:  # wstring
                    (value,) = struct.unpack("<Q", filestream.read(8))
                case _:
                    raise NotImplementedError(f"{value} not implemented")
            self.attributes.append(value)

    def writeAttributes(self, bytestream: bytearray, attributeHeaders):
        """extend and modify the bytearray by filling attributes"""
        self.attributesPH = list()
        for i, header in enumerate(attributeHeaders):
            value = ""
            match header["valueType"]:
                case -1:  # null wstring
                    value = struct.pack("<q", -1)
                case 0:  # int64
                    value = struct.pack("<q", self.attributes[i])
                case 1:  # double
                    value = struct.pack("<d", self.attributes[i])
                case 2:  # wstring
                    value = struct.pack("<q", -1)
            self.attributesPH.append(len(bytestream))
            bytestream.extend(value)

    def setName(self, name: str):
        """set entry name"""
        self.name = name

    def setContent(self, langs: list[str]):
        """set entry contents"""
        self.langs = langs

    def buildEntry(self, guid: str, crc: int, name: str, attributeValues: list, langs: list[str], hash: int = 0, index: int = 0):
        """use for file modification"""
        self.guid = uuid.UUID(hex=guid)
        self.crc = crc
        if isVersionEntryByHash(self.version):
            self.hash = hash
        else:
            self.index = index

        self.name = name
        self.attributes = list()
        for value in attributeValues:
            self.attributes.append(value)

        self.langs = langs


class MSG:
    """MSG object"""

    def __init__(self):
        pass

    def readMSG(self, filestream: io.BufferedReader):
        """read msg file and store info into this MSG object"""

        # header
        (version,) = struct.unpack("<I", filestream.read(4))
        (magic,) = struct.unpack("<4s", filestream.read(4))
        (headerOffset,) = struct.unpack("<Q", filestream.read(8))
        (entryCount,) = struct.unpack("<I", filestream.read(4))
        (attributeCount,) = struct.unpack("<I", filestream.read(4))
        (langCount,) = struct.unpack("<I", filestream.read(4))
        pad_align_up(filestream, 8)  # pad to 8
        if isVersionEncrypt(version):
            (dataOffset,) = struct.unpack("<Q", filestream.read(8))
        (unknDataOffset,) = struct.unpack("<Q", filestream.read(8))
        (langOffset,) = struct.unpack("<Q", filestream.read(8))
        (attributeOffset,) = struct.unpack("<Q", filestream.read(8))
        (attributeNameOffset,) = struct.unpack("<Q", filestream.read(8))

        # entries headers' offset
        entryOffsets: list[int] = list()
        for _ in range(entryCount):
            entryOffsets.append(struct.unpack("<Q", filestream.read(8))[0])

        # always 64bit null
        assert unknDataOffset == filestream.tell(), f"expected unknData at {unknDataOffset} but at {filestream.tell()}"
        (unknData,) = struct.unpack("<Q", filestream.read(8))
        assert unknData == 0, f"unknData should be 0 but found {unknData}"

        # indexes of all lang (follow via.Language)
        assert langOffset == filestream.tell(), f"expected languages at {langOffset} but at {filestream.tell()}"
        languages: list[int] = list()
        for _ in range(langCount):
            languages.append(struct.unpack("<I", filestream.read(4))[0])
        if not all([x in LANG_LIST.keys() and i == x for i, x in enumerate(languages)]):
            print(f"unkn lang found. {str(languages)}. Please update LANG_LIST from via.Language")

        # pad to 8
        pad_align_up(filestream, 8)

        # get attribute headers, get type of each attr
        assert attributeOffset == filestream.tell(), f"expected attributeValueTypes at {attributeOffset} but at {filestream.tell()}"
        attributeHeaders: list[dict] = list()
        for i in range(attributeCount):
            attributeHeaders.append(dict(valueType=struct.unpack("<i", filestream.read(4))[0]))

        # pad to 8
        pad_align_up(filestream, 8)

        # get attribute headers' name but hold the offset at attributeNamesOffsets. string reading will do after decrypt.
        assert attributeNameOffset == filestream.tell(), f"expected attributeNamesOffset at {attributeNameOffset} but at {filestream.tell()}"
        attributeNamesOffsets = list()
        for _ in range(attributeCount):
            attributeNamesOffsets.append(struct.unpack("<Q", filestream.read(8))[0])

        # get info(entry head) of each entry
        entrys: list[Entry] = list()
        for entryIndex in range(entryCount):
            assert entryOffsets[entryIndex] == filestream.tell(), f"expected entryOffsets[{entryIndex}] at {entryOffsets[entryIndex]} but at {filestream.tell()}"
            entry = Entry(version)
            entry.readHead(filestream, langCount)
            entrys.append(entry)

        # get attributes of each entry
        for entry in entrys:
            assert entry.attributeOffset == filestream.tell(), f"expected entry.attributeOffset at {self.attributeOffset} but at {filestream.tell()}"
            entry.readAttributes(filestream, attributeHeaders)

        # read / decrypt string pool
        if isVersionEncrypt(version):
            assert dataOffset == filestream.tell(), f"expected dataOffset at {dataOffset} but at {filestream.tell()}"
        else:
            dataOffset = filestream.tell()
        filestream.seek(0, 2)  # EOF
        dataSize = filestream.tell() - dataOffset
        assert dataSize % 2 == 0, f"wstring pool size should be even: {dataSize}"
        filestream.seek(dataOffset)  # start of string pool
        data = filestream.read(dataSize)
        if isVersionEncrypt(version):
            wcharPool = helper.decrypt(data)
        else:
            wcharPool = data
        stringDict = helper.wcharPool2StrDict(wcharPool)

        # read attribute name to attributeHeaders
        for i, attrHead in enumerate(attributeHeaders):
            attrHead["name"] = helper.seekString((attributeNamesOffsets[i] - dataOffset), stringDict)

        # get content of each entry
        for entryIndex, entry in enumerate(entrys):
            # set entry name
            entry.setName(helper.seekString((entry.entryNameOffset - dataOffset), stringDict))
            if isVersionEntryByHash(version):
                nameHash = mmh3.hash(key=entry.name.encode("utf-16-le"), seed=-1, signed=False)
                assert nameHash == entry.hash, f"expected {entry.hash} for {entry.name} but get {nameHash}"
            else:
                assert entryIndex == entry.index, f"expected {entryIndex} for {entry.name} but get {entry.index}"

            # set content by each lang
            lang = list()
            for strOffset in entry.contentOffsetsByLangs:
                lang.append(helper.seekString((strOffset - dataOffset), stringDict))
            entry.setContent(lang)

            # seek string value of each attribute
            for i, attrHead in enumerate(attributeHeaders):
                if attrHead["valueType"] == 2:
                    entry.attributes[i] = helper.seekString((entry.attributes[i] - dataOffset), stringDict)
                elif attrHead["valueType"] == -1:
                    temp = helper.seekString((entry.attributes[i] - dataOffset), stringDict)
                    assert temp == "" or temp == "\x00", f"attr value type -1 contain non-null value {temp}"
                    entry.attributes[i] = temp

        self.entrys: list[Entry] = entrys
        self.attributeHeaders: list[dict] = attributeHeaders
        self.version: int = version
        self.languages: list[int] = languages

        # debug use, to let input output stringpool keeps same
        # self.stringDict = stringDict

    def writeMSG(self) -> bytes:
        """write a msg file(bytes) from this object's info"""

        # header
        newFile = bytearray()
        newFile.extend(struct.pack("<I", self.version))
        newFile.extend(struct.pack("<4s", b"GMSG"))
        newFile.extend(struct.pack("<Q", 16))
        entryCount = len(self.entrys)
        newFile.extend(struct.pack("<I", entryCount))
        attributeCount = len(self.attributeHeaders)
        newFile.extend(struct.pack("<I", attributeCount))
        langCount = len(self.languages)
        newFile.extend(struct.pack("<I", langCount))
        newFile.extend(b"\x00" * (len(newFile) % 8))  # pad to 8
        if isVersionEncrypt(self.version):
            dataOffsetPH = len(newFile)
            newFile.extend(struct.pack("<q", -1))
        unknDataOffsetPH = len(newFile)
        newFile.extend(struct.pack("<q", -1))
        langOffsetPH = len(newFile)
        newFile.extend(struct.pack("<q", -1))
        attributeOffsetPH = len(newFile)
        newFile.extend(struct.pack("<q", -1))
        attributeNameOffsetPH = len(newFile)
        newFile.extend(struct.pack("<q", -1))

        # entries headers' offset
        entryOffsetsPH: list[int] = list()
        for _ in range(entryCount):
            entryOffsetsPH.append(len(newFile))
            newFile.extend(struct.pack("<q", -1))

        newFile[unknDataOffsetPH : unknDataOffsetPH + 8] = struct.pack("<Q", len(newFile))
        newFile.extend(struct.pack("<Q", 0))  # unknData
        newFile[langOffsetPH : langOffsetPH + 8] = struct.pack("<Q", len(newFile))
        newFile.extend(struct.pack("<" + "I" * langCount, *self.languages))  # languages

        newFile.extend(b"\x00" * (len(newFile) % 8))  # pad to 8
        newFile[attributeOffsetPH : attributeOffsetPH + 8] = struct.pack("<Q", len(newFile))
        newFile.extend(struct.pack("<" + "i" * attributeCount, *list([head["valueType"] for head in self.attributeHeaders])))  # attributeHeaders.valueType
        newFile.extend(b"\x00" * (len(newFile) % 8))  # pad to 8
        newFile[attributeNameOffsetPH : attributeNameOffsetPH + 8] = struct.pack("<Q", len(newFile))
        attributeNamesOffsetsPH: list[int] = list()
        for _ in range(attributeCount):
            attributeNamesOffsetsPH.append(len(newFile))
            newFile.extend(struct.pack("<q", -1))

        # info(entry head) of each entry
        for i, entry in enumerate(self.entrys):
            newFile[entryOffsetsPH[i] : entryOffsetsPH[i] + 8] = struct.pack("<Q", len(newFile))
            entry.writeHead(newFile)

        # attributes of each entry
        for i, entry in enumerate(self.entrys):
            newFile[entry.attributeOffsetPH : entry.attributeOffsetPH + 8] = struct.pack("<Q", len(newFile))
            entry.writeAttributes(newFile, self.attributeHeaders)

        # read / decrypt string pool
        dataOffset = len(newFile)
        if isVersionEncrypt(self.version):
            newFile[dataOffsetPH : dataOffsetPH + 8] = struct.pack("<Q", len(newFile))

        # construct string pool
        stringPoolSet = set()
        isStrAttrIdx = list()
        isNullAttrIdx = list()
        for i, a in enumerate(self.attributeHeaders):
            if a["valueType"] == -1:
                stringPoolSet.add("")
                isNullAttrIdx.append(i)
            elif a["valueType"] == 2:
                isStrAttrIdx.append(i)

        stringPoolSet.update([a["name"] for a in self.attributeHeaders])
        for entry in self.entrys:
            stringPoolSet.add(entry.name)
            stringPoolSet.update([entry.langs[lang] for lang in self.languages])
            stringPoolSet.update([entry.attributes[idx] for idx in isStrAttrIdx])

        strOffsetDict = helper.calcStrPoolOffsets(stringPoolSet)  # not doing string processing here, as it will change the key.
        # debug use, to let input output stringpool keeps same
        # strOffsetDict = dict((v,k) for k,v in self.stringDict.items())
        wcharPool = b"".join(helper.toWcharBytes(x) for x in strOffsetDict.keys())

        if isVersionEncrypt(self.version):
            newFile.extend(helper.encrypt(wcharPool))
        else:
            newFile.extend(wcharPool)

        # update string offsets
        for i, a in enumerate(self.attributeHeaders):
            newFile[attributeNamesOffsetsPH[i] : attributeNamesOffsetsPH[i] + 8] = struct.pack("<Q", strOffsetDict[a["name"]] + dataOffset)
        for entry in self.entrys:
            newFile[entry.entryNameOffsetPH : entry.entryNameOffsetPH + 8] = struct.pack("<Q", strOffsetDict[entry.name] + dataOffset)
            for lang in self.languages:
                newFile[entry.contentOffsetsByLangsPH[lang] : entry.contentOffsetsByLangsPH[lang] + 8] = struct.pack("<Q", strOffsetDict[entry.langs[lang]] + dataOffset)
            for idx in isStrAttrIdx:
                newFile[entry.attributesPH[idx] : entry.attributesPH[idx] + 8] = struct.pack("<Q", strOffsetDict[entry.attributes[idx]] + dataOffset)
            for idx in isNullAttrIdx:
                newFile[entry.attributesPH[idx] : entry.attributesPH[idx] + 8] = struct.pack("<Q", strOffsetDict[""] + dataOffset)

        # printHexView(newFile)

        return bytes(newFile)
