import os
import logging
import argparse
import REMSGUtil
import sys
import mmh3
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def DebugTest(msg, filenameFull):
    REMSGUtil.exportCSV(msg, filenameFull+".csv")
    REMSGUtil.exportTXT(msg, filenameFull+".txt", 0)
    REMSGUtil.exportJson(msg, filenameFull+".json")

    csvmsg = REMSGUtil.importCSV(msg, filenameFull+".csv")
    txtmsg = REMSGUtil.importTXT(msg, filenameFull+".txt", 0)
    jsonmsg = REMSGUtil.importJson(msg, filenameFull+".json")
    assert mmh3.hash(csvmsg.writeMSG()) == mmh3.hash(txtmsg.writeMSG()) == mmh3.hash(jsonmsg.writeMSG()) == mmh3.hash(msg.writeMSG())
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
        csvmsg.entrys[0].langs[0] = "Modification魔改"
        txtmsg.entrys[0].langs[0] = "Modification魔改"
        jsonmsg.entrys[0].langs[0] = "Modification魔改"
        REMSGUtil.exportCSV(csvmsg, filenameFull+".mod.csv")
        REMSGUtil.exportTXT(txtmsg, filenameFull+".mod.txt", 0)
        REMSGUtil.exportJson(jsonmsg, filenameFull+".mod.json")
        
        mcsvmsg = REMSGUtil.importCSV(msg, filenameFull+".mod.csv")
        mtxtmsg = REMSGUtil.importTXT(msg, filenameFull+".mod.txt", 0)
        mjsonmsg = REMSGUtil.importJson(msg, filenameFull+".mod.json")
        assert mmh3.hash(mcsvmsg.writeMSG()) == mmh3.hash(mtxtmsg.writeMSG()) == mmh3.hash(mjsonmsg.writeMSG())
        REMSGUtil.exportMSG(mtxtmsg, filenameFull+".mod.new")

        modmsg = REMSGUtil.importMSG(filenameFull+".mod.new")
        modmsg.entrys[0].langs[0] = msg.entrys[0].langs[0]
        REMSGUtil.exportMSG(modmsg, filenameFull+".new")
        newmsg = REMSGUtil.importMSG(filenameFull+".new")
        assert mmh3.hash(msg.writeMSG()) == mmh3.hash(newmsg.writeMSG())

    REMSGUtil.printAllAttr(msg, filenameFull)
    REMSGUtil.searchEntryName(msg, filenameFull, 'ep_qn')
    REMSGUtil.exportMHRTextDump(msg, filenameFull)
    REMSGUtil.searchAttrTy(msg, filenameFull, -1)
    REMSGUtil.searchSameGuid(msg, filenameFull)

def isValidMsgName(name: str) -> bool:
    return re.search(r"\.msg(\.\d+)?$", name, re.IGNORECASE) is not None

def getAllFileFromFolder(folderName : str, filetype = 'msg'):
    filetype = filetype.lower()
    filenameList = []
    for file in os.listdir(folderName):
        if filetype == "msg":
            if isValidMsgName(file):
                filenameList.append(os.path.join(folderName,file))
        elif file.lower().endswith('.'+filetype) and '.msg.' in file.lower():
            filenameList.append(os.path.join(folderName,file))
    
    return filenameList

def fillList(path: str, filetype = 'msg'):
    path = os.path.abspath(path)
    filetype = filetype.lower()
    if os.path.isdir(path):
        return getAllFileFromFolder(path, filetype)
    elif os.path.isfile(path):
        if filetype == 'msg':
            if isValidMsgName(path):
                return [path,]
        elif path.lower().endswith('.'+filetype):
            return [path,]
    return []

def worker(item, mode = "csv", modFile: str = None, lang : int = REMSGUtil.SHORT_LANG_LU["ja"], **kwargs):
    try:
        filenameFull = os.path.abspath(item)
        print("processing:"+filenameFull)
        
        msg = REMSGUtil.importMSG(filenameFull)
        # DebugTest(msg,filenameFull)
        
        if mode == "csv":
            if modFile is None:
                REMSGUtil.exportCSV(msg, filenameFull+'.'+mode)
            else:
                REMSGUtil.exportMSG(msg=REMSGUtil.importCSV(msg, modFile), filename=filenameFull+'.new')

        elif mode == "txt":
            if modFile is None:
                REMSGUtil.exportTXT(msg, filenameFull+'.'+mode, lang, encode=kwargs["txtformat"])
            else:
                REMSGUtil.exportMSG(msg=REMSGUtil.importTXT(msg, modFile, lang, encode=kwargs["txtformat"]), filename=filenameFull+'.new')

        elif mode == "json":
            if modFile is None:
                REMSGUtil.exportJson(msg, filenameFull+'.'+mode)
            else:
                REMSGUtil.exportMSG(msg=REMSGUtil.importJson(msg, modFile), filename=filenameFull+'.new')

        elif mode == "dump":
            REMSGUtil.exportMHRTextDump(msg, filenameFull+'.txt')


    except Exception as e:
        print(f'error with file {item}')
        # print(traceback.format_exc())
        logger.exception(e)

def main():
    parser = argparse.ArgumentParser(
                    prog = 'REMSG_Converter.exe',
                    description = 'Encode / Decode .msg file from RE Engine',
                    epilog = "https://github.com/dtlnor/REMSG_Converter")
    parser.add_argument('-i', '--input', type=str, help='input msg file or folder')
    parser.add_argument('-x', '--multiprocess', type=int, default=4, help='when you input multiple files by input a folder. How many process use to convert the files')
    parser.add_argument('-m', '--mode', type=str, choices=['csv','txt','json'], default='csv', help='choose output file format.\n  txt = msg tool style txt.\n  csv = all lang in one csv with rich info.\n  json = all lang in one json with rich info in mhrice format')
    parser.add_argument('-e', '--edit', type=str, help='input (csv/txt/json) file to edit the content.\n  if input as folder, the filename and number of files\n  should be same as original .msg file\n  (with corresponding (.txt/.csv/.json) extension)')
    parser.add_argument('-l', '--lang', type=str, default='ja', choices=REMSGUtil.SHORT_LANG_LU.keys(), help='input the lang you want to export for txt mode (default ja)\n')
    parser.add_argument('-f', '--txtformat', type=str, default=None, choices=['utf-8', 'utf-8-sig'], help="force txt read/write format to be 'utf-8' or 'utf-8-sig'(BOM).\n")
    parser.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    # print('\n'.join([REMSGUtil.LANG_LIST.get(v,f"lang_{v}")+": "+k for k, v in REMSGUtil.SHORT_LANG_LU.items()]))

    filenameList = []
    editList = []

    editMode = args.edit is not None

    if args.input is not None:
        filenameList = fillList(args.input)
        if args.edit is not None:
            editList = fillList(args.edit, args.mode)

    elif args.edit is not None: # input is none
        filenameList = []
        editList = fillList(args.edit, args.mode)
        # fill file list by edit list
        for file in list(editList):
            filename, file_extension = os.path.splitext(file)
            if os.path.exists(filename):
                filenameList.append(filename)
            else:
                print(f"{filename} not found, skiping this file...")
                editList.remove(file)

    else: # input is none
        remainder = args.args
        if (remainder is None) or (len(remainder) <= 0) or (len(remainder) > 2):
            pass
            # open without any args
            parser.print_help()
            input('\nincorrect args, press enter to exit...')
            sys.exit()

            # debug script input
            # filenameList = getAllFileFromFolder(r"C:\MyProgram\REText\msgFiles")
            # args.mode = "dump"
            # filenameList = [r"C:\MyProgram\REText\msgFiles\nid004.msg.539100710",]

        # guessing input... why am I doing this
        elif len(remainder) == 1:
            filenameList = fillList(remainder[0])

        elif len(remainder) == 2:
            msgList1 = fillList(remainder[0], 'msg')
            msgList2 = fillList(remainder[1], 'msg')
            editList1 = fillList(remainder[0], args.mode)
            editList2 = fillList(remainder[1], args.mode)

            filenameList = max([msgList1, msgList2], key=len)
            editList = max([editList1, editList2], key=len)

            editMode = True

    # after getting file list...
    if len(editList) <= 0:
        editList = list([None for _ in filenameList])
    elif len(editList) > 1:
        editfolder, name = os.path.split(editList[0])
        editList = []
        editFiles = dict([(f.lower(), f) for f in os.listdir(editfolder)])
        # find valid file - edit pair
        for file in list(filenameList):
            msgfolder, name = os.path.split(file)
            if (name+'.'+args.mode).lower() in editFiles:
                editList.append(os.path.join(editfolder,editFiles[(name+'.'+args.mode).lower()]))
            else:
                print(f"{name}.{args.mode} not found, skiping this file...")
                filenameList.remove(file)

    if len(filenameList) <= 0:
        print(f"No valid input file, exiting.")
        sys.exit(1)
    
    if editMode and (len(editList) <= 0 or None in editList):
        print(f"{args.mode} mode with edit file/folder input but no {args.mode} file found.")
        sys.exit(1)

    executor = concurrent.futures.ProcessPoolExecutor(args.multiprocess)
    futures = [executor.submit(worker, file, mode = args.mode, modFile = edit, lang = REMSGUtil.SHORT_LANG_LU[args.lang], txtformat=args.txtformat) for file, edit in zip(filenameList, editList)]
    concurrent.futures.wait(futures)

if __name__ == "__main__":
    # import threading
    import multiprocessing
    import concurrent.futures
    multiprocessing.freeze_support()
    main()