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

import json

ENUM_FILE = R"..\MHWs-in-json\Enums_Internal.json"
ENEMY_COUNT_FILE = R"..\MHWs-in-json\natives\STM\GameDesign\Common\Text\EnemyCountData.user.3.json"

enum_data: dict = {}
enemy_count_index: dict = {}

# Maps message language id → EnemyCountData field name
LANG_TO_COUNTTYPE_FIELD: dict[str, str] = {
    "ja":   "_CountTypeJP",
    "ko":   "_CountTypeKO",
    "zhtw": "_CountTypeTW",
    "zhcn": "_CountTypeCN",
}


def load_global_data():
    global enum_data, enemy_count_index
    with open(ENUM_FILE, "r", encoding="utf-8") as f:
        enum_data = json.load(f)
    with open(ENEMY_COUNT_FILE, "r", encoding="utf-8") as f:
        enemy_count_data = json.load(f)
    # Build a fast lookup: stripped EM id → cData dict
    re_strip_prefix = re.compile(r"^\[.*?\]")
    for item in enemy_count_data[0]["app.user_data.EnemyCountData"]["_Values"]:
        cdata = item["app.user_data.EnemyCountData.cData"]
        em_id = re_strip_prefix.sub("", cdata["_EnemyId"])
        enemy_count_index[em_id] = cdata


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


re_xref_id = re.compile(r"((?<!&)<[Rr][Ee][Ff] (.*?)(?<!&)>)")
re_xref_em_id = re.compile(r"((?<!&)<EMID (.*?)(?<!&)>)")
re_xref_em_jp = re.compile(r"((?<!&)<EMIDJP (.*?)(?<!&)>)")
re_xref_em_ct = re.compile(r"((?<!&)<EMCT (.*?)(?<!&)>)")
# re_text_remain = re.compile(r"((?<!&)<(?!/?(?:EMID|EMIDJP|EMCT|[Rr][Ee][Ff]|C[Oo][Ll][Oo][Rr]|ICON|EMPARAM|STYLE|BOLD|ITALIC|LSNR|INPUTMSG|SPKR|PLNAME|OTNAME|PLURAL|PLATMSG|NUMBER|FSR|XESS|DLSS|OPTION|DATETIME|[rR][tT][lL]|[lL][tT][rR]|CENTER|a|LOWER|LEFT|VARIOUS|Accent|BLS)[\s>])(.*?)(?<!&)>)")
re_count_num = re.compile(r"COUNT_(\d+)$")


def _make_emid_tag(xref_name: str, _: str) -> str:
    if "EM0070_00_0 CLB_01" in xref_name:
        return "EnemyText_EXTRA_NAME_EM0070_00_0"
    if "EM0150_00_0 EX" in xref_name or 'EM0150_00_0 "EX"' in xref_name:
        return "EnemyText_EXTRA_NAME_EM0150_00_0"
    if " FR" in xref_name:
        return f"EnemyText_FRENZY_NAME_{xref_name.split()[0]}"
    return f"EnemyText_NAME_{xref_name}"


def _make_emct_tag(xref_name: str, lang_id: str) -> str | None:
    count_field = LANG_TO_COUNTTYPE_FIELD.get(lang_id)
    if count_field is None:
        return None
    cdata = enemy_count_index.get(xref_name)
    if cdata is None:
        logger.warning(f"Enemy count data not found for EM id: {xref_name}")
        return None
    m = re_count_num.search(cdata.get(count_field, ""))
    if not m:
        logger.warning(f"Count type not found in enemy count data for EM id: {xref_name}")
        return None
    return f"Localize_0000_{int(m.group(1)):03d}"


_XREF_RESOLVERS = [
    (re_xref_id,    lambda name, _: name),
    (re_xref_em_id, _make_emid_tag),
    (re_xref_em_jp, lambda name, _: f"EnemyText_JP_NAME_{name}"),
    (re_xref_em_ct, _make_emct_tag),
]


def process_xref(db_entries: dict[str, dict]) -> dict[str, dict]:
    name_index = {entry["name"]: entry for entry in db_entries.values()}
    for guid, entry in list(db_entries.items()):
        db_entries[guid] = replace_xref_tag_in_entry(entry, name_index)
    return db_entries


def replace_xref_tag_in_entry(entry: dict, name_index: dict[str, dict]) -> dict:
    for i, content in entry["content"].items():
        entry["content"][i] = replace_xref_tag_in_content(content, i, name_index)
    return entry


def replace_xref_tag_in_content(content: str, lang_id: str, name_index: dict[str, dict], _seen: frozenset = frozenset()) -> str:
    for xref_regex, tag_fn in _XREF_RESOLVERS:
        for xref_tag, xref_name in xref_regex.findall(content):
            if "{" in xref_name or "}" in xref_name:
                continue
            tag = tag_fn(xref_name, lang_id)
            if tag is None or tag in _seen:
                continue
            entry = name_index.get(tag)
            if entry:
                return replace_xref_tag_in_content(
                    content.replace(xref_tag, entry["content"][lang_id], 1),
                    lang_id, name_index, _seen | {tag},
                )
            logger.warning(f"Xref entry not found: {tag!r} (from {xref_tag!r})")
    return content


SHORT_LANG_LU_REV = {REMSGUtil.SHORT_LANG_LU[k]: k for k in REMSGUtil.SHORT_LANG_LU}


def all_in_one_worker(item, folderprefix, versionsuffix):
    try:
        filenameFull = Path(item).absolute()
        print("processing:" + str(filenameFull))

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

        relative_path = filenameFull.relative_to(folderprefix)
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
    load_global_data()

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


if __name__ == "__main__":
    # import threading
    import concurrent.futures
    import multiprocessing

    multiprocessing.freeze_support()

    # infolder should contains all the msg.23 files
    infolder = R"G:\MHWs\natives\STM"
    outfolder = R"G:\MHWs\msg\natives\STM"

    ####################################################
    # # dump all json files in folder
    # filenameList, editList = getFolders(infolder, outfolder)

    # multiprocess = 4
    # executor = concurrent.futures.ProcessPoolExecutor(multiprocess)
    # futures = [executor.submit(worker, file, outfile=edit) for file, edit in zip(filenameList, editList)]
    # concurrent.futures.wait(futures)

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

    infolder = Path(R"..\MHWs-in-json\natives\STM").absolute()
    filenameList = [os.path.join(dp, f) for dp, dn, filenames in os.walk(infolder) for f in filenames if f.endswith(".msg.23.json")]
    dumpAllInOneJson(filenameList, R"..\dtlnor-mhws-scripts\1.041.msg.json", folderprefix=infolder, versionsuffix=".23.json")

    ###################################################
    print("All Done.")
