import argparse
import logging
import re
import sys

import mmh3
import REMSGUtil
from typing import List
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


errorFileList = {}


isValidMsgNameRegex = re.compile(r"\.msg.*(?<!\.txt)(?<!\.json)(?<!\.csv)$", re.IGNORECASE)
def isValidMsgName(name: str) -> bool:
    return isValidMsgNameRegex.search(name) is not None


def getAllFileFromFolder(folder: Path, filetype: str = "msg") -> List[Path]:
    filetype = filetype.lower()
    if filetype == "msg":
        return [f for f in folder.rglob("*") if f.is_file() and isValidMsgName(f.name)]
    else:
        return [f for f in folder.rglob(f"*.{filetype}") if f.is_file() and ".msg." in f.name.lower()]


def fillList(inpath: str | Path, filetype: str = "msg") -> List[Path]:
    path = Path(inpath).resolve()
    filetype = filetype.lower()
    if path.is_dir():
        return getAllFileFromFolder(path, filetype)
    elif path.is_file():
        if filetype == "msg":
            if isValidMsgName(path.name):
                return [path]
        elif path.suffix.lower() == "." + filetype:
            return [path]
    return []


def worker(item: Path, mode: str = "csv", modFile: Path | None = None, lang: int = REMSGUtil.SHORT_LANG_LU["ja"], **kwargs) -> None:
    try:
        filenameFull = str(item.resolve())
        modFile = str(modFile.resolve()) if modFile is not None else None
        print("processing:" + filenameFull)

        msg = REMSGUtil.importMSG(filenameFull)

        if mode == "csv":
            if modFile is None:
                REMSGUtil.exportCSV(msg, filenameFull + "." + mode)
            else:
                REMSGUtil.exportMSG(msg=REMSGUtil.importCSV(msg, modFile), filename=filenameFull + ".new")

        elif mode == "txt":
            if modFile is None:
                REMSGUtil.exportTXT(msg, filenameFull + "." + mode, lang, encode=kwargs["txtformat"], withEntryName=kwargs["entryName"])
            else:
                REMSGUtil.exportMSG(msg=REMSGUtil.importTXT(msg, modFile, lang, encode=kwargs["txtformat"]), filename=filenameFull + ".new")

        elif mode == "json":
            if modFile is None:
                REMSGUtil.exportJson(msg, filenameFull + "." + mode)
            else:
                REMSGUtil.exportMSG(msg=REMSGUtil.importJson(msg, modFile), filename=filenameFull + ".new")

        elif mode == "dump":
            REMSGUtil.exportMHRTextDump(msg, filenameFull + ".txt")

    except Exception as e:
        print(f"error with file {item}")
        # print(traceback.format_exc())
        logger.exception(e)
        errorFileList[item] = str(e)

def getFolders(parser: argparse.ArgumentParser) -> tuple[List[Path], List[Path | None]]:
    args = parser.parse_args()

    filenameList = []
    editList = []

    editMode = args.edit is not None

    if args.input is not None:
        filenameList = fillList(args.input)
        if args.edit is not None:
            editList = fillList(args.edit, args.mode)

    elif args.edit is not None:  # input is none
        filenameList = []
        editList = fillList(args.edit, args.mode)
        # fill file list by edit list
        for file in list(editList):
            msg_file = file.stem
            if msg_file.exists():
                filenameList.append(msg_file)
            else:
                print(f"{msg_file} not found, skiping this file...")
                editList.remove(file)

    else:  # input is none
        remainder = args.args
        if (remainder is None) or (len(remainder) <= 0) or (len(remainder) > 2):
            pass
            # open without any args
            parser.print_help()
            input("\nincorrect args, press enter to exit...")
            sys.exit()

        # guessing input... why am I doing this
        elif len(remainder) == 1:
            filenameList = fillList(remainder[0])

        elif len(remainder) == 2:
            msgList1 = fillList(remainder[0], "msg")
            msgList2 = fillList(remainder[1], "msg")
            editList1 = fillList(remainder[0], args.mode)
            editList2 = fillList(remainder[1], args.mode)

            filenameList = max([msgList1, msgList2], key=len)
            editList = max([editList1, editList2], key=len)

            editMode = True

    # after getting file list...
    if len(editList) <= 0:
        editList = [None for _ in filenameList]
    elif len(editList) > 1:
        editfolder = editList[0].parent
        editList = []
        editFiles = {f.name.lower(): f for f in editfolder.iterdir()}
        # find valid file - edit pair
        for file in filenameList:
            if (file.name + "." + args.mode).lower() in editFiles:
                editList.append(editFiles[(file.name + "." + args.mode).lower()])
            else:
                print(f"{file.name}.{args.mode} not found, skiping this file...")
                filenameList.remove(file)

    if len(filenameList) <= 0:
        print("No valid input file, exiting.")
        sys.exit(1)

    if editMode and (len(editList) <= 0 or None in editList):
        print(f"{args.mode} mode with edit file/folder input but no {args.mode} file found.")
        sys.exit(1)

    return filenameList, editList

def main():
    parser = argparse.ArgumentParser(
                    prog = 'REMSG_Converter.exe',
                    description = 'Encode / Decode .msg file from RE Engine',
                    epilog = "https://github.com/dtlnor/REMSG_Converter")
    parser.add_argument("-i", "--input", type=str,
                        help="input msg file or folder")
    parser.add_argument("-x", "--multiprocess", type=int, default=4,
                        help="when you are processing multiple files. How many processes to use to convert the files")
    parser.add_argument("-m", "--mode", type=str, choices=["csv", "txt", "json"], default="csv",
                        help="choose output file format.\n  txt = msg tool style txt.\n  csv = all lang in one csv with rich info.\n  json = all lang in one json with rich info in mhrice format")
    parser.add_argument("-e", "--edit", type=str,
                        help="input (csv/txt/json) file to edit the content.\n  if input as folder, the filename and number of files\n  should be same as original .msg file\n  (with corresponding (.txt/.csv/.json) extension)")
    parser.add_argument("-l", "--lang", type=str, default="ja", choices=REMSGUtil.SHORT_LANG_LU.keys(),
                        help="input the lang you want to export for txt mode (default ja)\n")
    parser.add_argument("-f", "--txtformat", type=str, default=None, choices=["utf-8", "utf-8-sig"],
                        help="force txt read/write format to be 'utf-8' or 'utf-8-sig'(BOM).\n")
    parser.add_argument("-n", "--entryName", action='store_true', default=False,
                        help="Also export the entry name to txt file.\n")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    # print('\n'.join([REMSGUtil.LANG_LIST.get(v,f"lang_{v}")+": "+k for k, v in REMSGUtil.SHORT_LANG_LU.items()]))

    errorFileList = {}
    filenameList, editList = getFolders(parser)

    executor = concurrent.futures.ProcessPoolExecutor(args.multiprocess)
    futures = [executor.submit(worker, file, mode=args.mode, modFile=edit, lang=REMSGUtil.SHORT_LANG_LU[args.lang], txtformat=args.txtformat, entryName=args.entryName) for file, edit in zip(filenameList, editList)]
    concurrent.futures.wait(futures)

    if len(errorFileList) > 0:
        print("Failed file summary:")
        for file, error in errorFileList.items():
            print(f"{file}: {error}")

    print("All Done.")


if __name__ == "__main__":
    # import threading
    import concurrent.futures
    import multiprocessing

    multiprocessing.freeze_support()
    main()
