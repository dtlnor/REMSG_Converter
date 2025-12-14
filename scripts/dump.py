import argparse
import logging
import os
import re
import sys
from pathlib import Path
import mmh3

sys.path.append(str(Path(__file__).parent.parent / "src"))
import REMSGUtil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


isValidMsgNameRegex = re.compile(r"\.msg.*(?<!\.txt)(?<!\.json)(?<!\.csv)$", re.IGNORECASE)


def isValidMsgName(name: str) -> bool:
    return isValidMsgNameRegex.search(name) is not None


def getAllFileFromFolder(folderName: str, filetype="msg"):
    filetype = filetype.lower()
    filenameList = []
    for file in os.listdir(folderName):
        if filetype == "msg":
            if isValidMsgName(file):
                filenameList.append(os.path.join(folderName, file))
        elif file.lower().endswith("." + filetype) and ".msg." in file.lower():
            filenameList.append(os.path.join(folderName, file))

    return filenameList


def fillList(path: str, filetype="msg"):
    path = os.path.abspath(path)
    filetype = filetype.lower()
    if os.path.isdir(path):
        return getAllFileFromFolder(path, filetype)
    elif os.path.isfile(path):
        if filetype == "msg":
            if isValidMsgName(path):
                return [
                    path,
                ]
        elif path.lower().endswith("." + filetype):
            return [
                path,
            ]
    return []


def worker(infile, outfile: str = None):
    try:
        filenameFull = os.path.abspath(infile)
        outfileFull = os.path.abspath(outfile)
        Path(outfileFull).parent.mkdir(parents=True, exist_ok=True)

        print("processing:" + filenameFull)

        msg = REMSGUtil.importMSG(filenameFull)
        REMSGUtil.exportJson(msg, outfileFull)

    except Exception as e:
        print(f"error with file {infile}")
        # print(traceback.format_exc())
        logger.exception(e)


def dumpAlltxt(infile):
    try:
        filenameFull = os.path.abspath(infile)
        print("processing:" + filenameFull)

        msg = REMSGUtil.importMSG(filenameFull)

        REMSGUtil.exportMHRTextDump(msg, filenameFull + ".txt", False)
        REMSGUtil.exportCSV(msg, filenameFull + "." + "csv")

    except Exception as e:
        print(f"error with file {infile}")
        # print(traceback.format_exc())
        logger.exception(e)


def getFolders(infolder: str, outfolder: str = None):
    filenameList = []
    filenameList = [os.path.join(dp, f) for dp, dn, filenames in os.walk(infolder) for f in filenames if f.endswith(".msg.23")]

    outfileList = []
    if outfolder is None:
        outfileList = [None for _ in filenameList]
    else:
        outfileList = [outfolder + filename.removeprefix(infolder) + ".json" for filename in filenameList]

    print(f"found {len(filenameList)} files in {infolder}")
    return filenameList, outfileList


re_xref_id = re.compile(r"(<[Rr][Ee][Ff] (.*?)>)")
re_xref_em_id = re.compile(r"(<EMID (.*?)>)")
re_xref_em_ct = re.compile(r"(<EMCT (.*?)>)")


def process_xref(db_entries: dict[str, dict]) -> dict[str, dict]:
    for entry in db_entries.values():
        new_entry = replace_xref_tag_in_entry(entry, db_entries)
        db_entries[entry["name"]] = new_entry
    return db_entries


def replace_xref_tag_in_entry(entry: dict, db_entries: dict[str, dict]) -> dict:
    for i, content in entry["contents"].items():
        content = replace_xref_tag_in_content(content, i, db_entries)
        entry["contents"][i] = content
    return entry


def replace_xref_tag_in_content(content: str, lang_id: int, db_entries: dict[str, dict]) -> str:
    line = content
    xrefs = re_xref_id.findall(line)
    for xref in xrefs:
        xref_tag = xref[0]
        xref_name = xref[1]
        xref_entry = db_entries.get(xref_name)
        if xref_entry:
            line = line.replace(xref_tag, xref_entry["contents"][lang_id], 1)
            line = replace_xref_tag_in_content(line, lang_id, db_entries)
    xrefs = re_xref_em_id.findall(line)
    for xref in xrefs:
        xref_tag = xref[0]
        xref_name = xref[1]
        tag = f"EnemyText_NAME_{xref_name}"
        xref_entry = db_entries.get(tag)
        if xref_entry:
            line = line.replace(xref_tag, xref_entry["contents"][lang_id], 1)
            line = replace_xref_tag_in_content(line, lang_id, db_entries)
    return line


SHORT_LANG_LU_REV = {REMSGUtil.SHORT_LANG_LU[k]: k for k in REMSGUtil.SHORT_LANG_LU}


def all_in_one_worker(item, folderprefix, versionsuffix):
    try:
        filenameFull = os.path.abspath(item)
        print("processing:" + filenameFull)

        msg = REMSGUtil.importJson(None, filenameFull)
        # DebugTest(msg,filenameFull)

        data = REMSGUtil.buildmhriceJson(msg)

        allinone = {}
        # get useful attributes
        attrIdx = {}
        for i, attr in enumerate(data["attribute_headers"]):
            if attr["ty"] not in [0, 1, 2]:
                continue
            attrIdx[i] = attr["name"]

        relative_path = Path(filenameFull).relative_to(folderprefix)
        belongs_to = str(relative_path.as_posix()).removesuffix(versionsuffix)

        for entries in data["entries"]:
            allinone[entries["guid"]] = {
                "name": entries["name"],
                "belongs_to": belongs_to,
                "attributes": {attrIdx[i]: list(value.values())[0] for i, value in enumerate(entries["attributes"]) if i in attrIdx},
                # "attributes": [{attrIdx[i]: list(value.values())[0]} for i, value in enumerate(entries["attributes"]) if i in attrIdx],
                # "attributes": {k: v for d in [{attrIdx[i]: list(value.values())[0]} for i, value in enumerate(entries["attributes"]) if i in attrIdx] for k, v in d.items()},
                # "content": {reversedSHORT_LANG_LU[lang]: entries["content"][lang] for lang in data["languages"] if lang >= 0},
                "content": {SHORT_LANG_LU_REV[lang]: entries["content"][lang] for lang in REMSGUtil.REMSG.MHR_SUPPORTED_LANG},
            }

    except Exception as e:
        print(f"error with file {item}")
        # print(traceback.format_exc())
        logger.exception(e)

    return allinone


def dumpAllInOneJson(filenameList: list, outputfile, folderprefix: str = None, versionsuffix: str = None):
    import json

    # filenameList = getAllFileFromFolder(folder, 'msg')

    executor = concurrent.futures.ProcessPoolExecutor(16)
    futures = [executor.submit(all_in_one_worker, file, folderprefix, versionsuffix) for file in filenameList]
    concurrent.futures.wait(futures)

    allinone = {}

    # merge all json return from futures into one
    for future in futures:
        allinone.update(future.result())

    # sort by "name"
    allinone = dict(sorted(allinone.items(), key=lambda item: item[1]["name"]))

    allinone = process_xref(allinone)

    # dump allinone
    with open(outputfile, "w", encoding="utf-8") as f:
        json.dump(allinone, f, ensure_ascii=False, indent=4)


def dump_text_db(filenameList: list, outputfile):
    import json

    executor = concurrent.futures.ProcessPoolExecutor(4)
    futures = [executor.submit(all_in_one_worker, file) for file in filenameList]
    concurrent.futures.wait(futures)

    allinone = {}

    # merge all json return from futures into one
    for future in futures:
        allinone.update(future.result())

    # sort by "name"
    allinone = dict(sorted(allinone.items(), key=lambda item: item[1]["name"]))

    # dump allinone
    with open(outputfile, "w", encoding="utf-8") as f:
        json.dump(allinone, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # import threading
    import concurrent.futures
    import multiprocessing

    multiprocessing.freeze_support()

    # infolder should contains all the msg.23 files
    infolder = R"G:\MHWs\natives\STM"
    outfolder = R"G:\MHWs\msg\natives\STM"

    ####################################################
    # dump all json files in folder
    filenameList, editList = getFolders(infolder, outfolder)

    multiprocess = 4
    executor = concurrent.futures.ProcessPoolExecutor(multiprocess)
    futures = [executor.submit(worker, file, outfile=edit) for file, edit in zip(filenameList, editList)]
    concurrent.futures.wait(futures)

    ####################################################
    # # dump all txt and csv files in folder

    # # get all msg.23 files from src folder
    # src = R"G:\MHWs\natives"
    # filenameList = [os.path.join(dp, f) for dp, dn, filenames in os.walk(src) for f in filenames if f.endswith(".msg.23")]
    # # copy paste the msg files to textFolder without the heirarchy
    # textFolder = R"G:\MHWs\text"
    # for file in filenameList:
    #     Path(textFolder).mkdir(parents=True, exist_ok=True)
    #     dest = os.path.join(textFolder, os.path.basename(file))
    #     if not os.path.exists(dest):
    #         os.link(file, dest)

    # filenameList, editList = getFolders(textFolder)

    # multiprocess = 4
    # executor = concurrent.futures.ProcessPoolExecutor(multiprocess)
    # futures = [executor.submit(dumpAlltxt, file) for file in filenameList]
    # concurrent.futures.wait(futures)

    ###################################################
    # import all json files in folder and dump all in one json

    infolder = R"..\MHWs-in-json\natives\STM"
    filenameList = [os.path.join(dp, f) for dp, dn, filenames in os.walk(infolder) for f in filenames if f.endswith(".msg.23.json")]
    dumpAllInOneJson(filenameList, R"..\dtlnor-mhws-scripts\1.030.msg.json", folderprefix=infolder, versionsuffix=".23.json")

    print("All Done.")
