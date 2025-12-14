import argparse
import logging
import os
import re
import sys
from pathlib import Path
import mmh3

sys.path.append(str(Path(__file__).parent.parent / "src"))
import REMSGUtil

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def DebugTest(msg, filenameFull):
    version = msg.version
    assert len(msg.languages) == REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version], f"msg version {version} language count mismatch, expect {REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version]}, got {len(msg.languages)}"

    REMSGUtil.exportCSV(msg, filenameFull + ".csv")
    REMSGUtil.exportTXT(msg, filenameFull + ".txt", 0)
    REMSGUtil.exportTXT(msg, filenameFull + "_name.txt", 0)
    REMSGUtil.exportJson(msg, filenameFull + ".json")

    csvmsg = REMSGUtil.importCSV(msg, filenameFull + ".csv")
    txtmsg = REMSGUtil.importTXT(msg, filenameFull + ".txt", 0)
    txtmsg2 = REMSGUtil.importTXT(msg, filenameFull + "_name.txt", 0)
    jsonmsg = REMSGUtil.importJson(msg, filenameFull + ".json")

    assert len(csvmsg.languages) == REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version], f"msg version {version} language count mismatch, expect {REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version]}, got {len(csvmsg.languages)}"
    assert len(txtmsg.languages) == REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version], f"msg version {version} language count mismatch, expect {REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version]}, got {len(txtmsg.languages)}"
    assert len(txtmsg2.languages) == REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version], f"msg version {version} language count mismatch, expect {REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version]}, got {len(txtmsg2.languages)}"
    assert len(jsonmsg.languages) == REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version], f"msg version {version} language count mismatch, expect {REMSGUtil.REMSG.VERSION_2_LANG_COUNT[version]}, got {len(jsonmsg.languages)}"

    # import HexTool as ht
    # print("csvmsg")
    # ht.printHexView(csvmsg.writeMSG())
    # print("txtmsg")
    # ht.printHexView(txtmsg.writeMSG())
    # print("txtmsg2")
    # ht.printHexView(txtmsg2.writeMSG())
    # print("jsonmsg")
    # ht.printHexView(jsonmsg.writeMSG())
    # REMSGUtil.exportMSG(jsonmsg, filenameFull + ".json.new")
    # print("msg")
    # ht.printHexView(msg.writeMSG())

    assert mmh3.hash(csvmsg.writeMSG()) == mmh3.hash(txtmsg.writeMSG()) == mmh3.hash(jsonmsg.writeMSG()) == mmh3.hash(msg.writeMSG()) == mmh3.hash(txtmsg2.writeMSG()), "import all format assert failed"
    # if not (mmh3.hash(csvmsg.writeMSG()) == mmh3.hash(txtmsg.writeMSG()) == mmh3.hash(jsonmsg.writeMSG()) == mmh3.hash(msg.writeMSG())):
    #     print(filenameFull,len(csvmsg.writeMSG()),len(txtmsg.writeMSG()),len(jsonmsg.writeMSG()),len(msg.writeMSG()) )
    #     # REMSGUtil.printHexView(csvmsg.writeMSG())
    #     # REMSGUtil.printHexView(txtmsg.writeMSG())
    #     # REMSGUtil.printHexView(jsonmsg.writeMSG())
    #     # REMSGUtil.exportJson(csvmsg, filenameFull+".csv.json")
    #     # REMSGUtil.exportJson(txtmsg, filenameFull+".txt.json")
    #     # REMSGUtil.exportJson(jsonmsg, filenameFull+".json.json")
    #     # REMSGUtil.exportMSG(csvmsg, filenameFull+".csv.new")
    #     # REMSGUtil.exportMSG(txtmsg, filenameFull+".txt.new")
    #     # REMSGUtil.exportMSG(jsonmsg, filenameFull+".json.new")
    #     # REMSGUtil.exportMSG(msg, filenameFull+".ori.new")
    if len(msg.entrys) > 1 and True:
        csvmsg.entrys[0].langs[0] = "Modification 魔改"
        txtmsg.entrys[0].langs[0] = "Modification 魔改"
        txtmsg2.entrys[0].langs[0] = "Modification 魔改"
        jsonmsg.entrys[0].langs[0] = "Modification 魔改"
        REMSGUtil.exportCSV(csvmsg, filenameFull + ".mod.csv")
        REMSGUtil.exportTXT(txtmsg, filenameFull + ".mod.txt", 0)
        REMSGUtil.exportTXT(txtmsg2, filenameFull + "_name.mod.txt", 0)
        REMSGUtil.exportJson(jsonmsg, filenameFull + ".mod.json")

        mcsvmsg = REMSGUtil.importCSV(msg, filenameFull + ".mod.csv")
        mtxtmsg = REMSGUtil.importTXT(msg, filenameFull + ".mod.txt", 0)
        mtxtmsg2 = REMSGUtil.importTXT(msg, filenameFull + "_name.mod.txt", 0)
        mjsonmsg = REMSGUtil.importJson(msg, filenameFull + ".mod.json")
        assert mmh3.hash(mcsvmsg.writeMSG()) == mmh3.hash(mtxtmsg.writeMSG()) == mmh3.hash(mjsonmsg.writeMSG()) == mmh3.hash(mtxtmsg2.writeMSG())
        REMSGUtil.exportMSG(mtxtmsg, filenameFull + ".mod.new")

        modmsg = REMSGUtil.importMSG(filenameFull + ".mod.new")
        modmsg.entrys[0].langs[0] = msg.entrys[0].langs[0]
        REMSGUtil.exportMSG(modmsg, filenameFull + ".new")
        newmsg = REMSGUtil.importMSG(filenameFull + ".new")
        assert mmh3.hash(msg.writeMSG()) == mmh3.hash(newmsg.writeMSG())

    allAttr = REMSGUtil.searchAllAttr(msg, filenameFull)
    entryNameToSearch = "ep_qn"
    entryName = REMSGUtil.searchEntryName(msg, filenameFull, entryNameToSearch)
    # REMSGUtil.exportMHRTextDump(msg, filenameFull)
    attrTy = REMSGUtil.searchAttrTy(msg, filenameFull, -1)
    sameGUID = REMSGUtil.searchSameGuid(msg)

    # print("Search All Attr:")
    # for line in allAttr:
    #     print(line)

    # print(f"Search Entry Name ('{entryNameToSearch}'):")
    # for line in entryName:
    #     print(line)

    print("Search Attr Type (-1):")
    for line in attrTy:
        print(line)

    print("Search Same GUID:")
    for line in sameGUID:
        print(line)


errorList = []


def worker(item):
    try:
        filenameFull = os.path.abspath(item)
        print("processing:" + filenameFull)

        msg = REMSGUtil.importMSG(filenameFull)
        DebugTest(msg, filenameFull)

    except Exception as e:
        print(f"error with file {item}")
        # print(traceback.format_exc())
        logger.exception(e)
        errorList.append((item, str(e)))


if __name__ == "__main__":
    # import threading
    import concurrent.futures
    import multiprocessing

    multiprocessing.freeze_support()

    # infolder = R".\REMSG_Converter_1.2.0\test\RE3_PS4_1.07"

    # filenameList = [os.path.join(dp, f) for dp, dn, filenames in os.walk(infolder) for f in filenames if f.endswith(".msg.67109135")]
    filenameList = [
        R".\scripts\1331076205-2347690482.msg.16777484",
    ]
    for i, filename in enumerate(filenameList):
        print(f"processing {i + 1}/{len(filenameList)}: {filename}")
        worker(filename)

    # print errorList
    if len(errorList) > 0:
        print("Errors occurred during processing:")
        for item, error in errorList:
            print(f"File: {item}, Error: {error}")

    # path = R".\REMSG_Converter_1.2.0\qu020030.msg.22"
    # msg = REMSGUtil.importMSG(path)
    # REMSGUtil.exportJson(msg, path + ".json")
    # REMSGUtil.exportCSV(msg, path + ".csv")
    # REMSGUtil.exportTXT(msg, path + ".txt", 21)

    # jsonmsg = REMSGUtil.importJson(msg, path + ".json")
    # assert mmh3.hash(msg.writeMSG()) == mmh3.hash(jsonmsg.writeMSG()), "json import/export failed"
    # csvmsg = REMSGUtil.importCSV(msg, path + ".csv")
    # assert mmh3.hash(msg.writeMSG()) == mmh3.hash(csvmsg.writeMSG()), "csv import/export failed"
    # txtmsg = REMSGUtil.importTXT(msg, path + ".txt", 21)
    # assert mmh3.hash(msg.writeMSG()) == mmh3.hash(txtmsg.writeMSG()), "txt import/export failed"
    # REMSGUtil.exportMSG(jsonmsg, path + ".json.new.msg.20")
    # REMSGUtil.exportMSG(csvmsg, path + ".csv.new.msg.20")
    # REMSGUtil.exportMSG(txtmsg, path + ".txt.new.msg.20")

    # path = R".\REMSG_Converter_1.2.0\1ui06073.msg.22"
    # worker(path)
    # msg = REMSGUtil.importMSG(path)
    # REMSGUtil.exportJson(msg, path + ".json")
    # REMSGUtil.exportCSV(msg, path + ".csv")
    # REMSGUtil.exportTXT(msg, path + ".txt", 21)
    # path = R".\REMSG_Converter_1.2.0\ui06073.msg.22"
    # msg = REMSGUtil.importMSG(path)
    # REMSGUtil.exportJson(msg, path + ".json")
    # REMSGUtil.exportCSV(msg, path + ".csv")
    # REMSGUtil.exportTXT(msg, path + ".txt", 21)

    # jsonpath = R".\REMSG_Converter_1.2.0\uk\ui06073.msg.22.json"
    # jsonmsg = REMSGUtil.importJson(None, jsonpath)
    # REMSGUtil.exportMSG(jsonmsg, jsonpath + ".new.msg.20")
