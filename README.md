# REMSG_Converter
 
 Python library for converting from RE engine msg text file to json/csv/txt and back.
 
# Description
 For txt, I let it stay similar format to the msg tool. That means one lang one txt file.
 
 For csv, I put all the languages into one file, with the msg entry name, its guid, and attributes.  
 I think this helps for research purposes.
 
 For json, I made it similar to mhrice's, but also added some file format information.  
 Thus json format can convert to msg on its own (but you still need to pass a dummy .msg file with json file together)  
 that means you can modify the attribute, guid, and number of entries, for json file modification.  
 (but IDK if the game works fine when you add/delete an entry for the existing msg)  
 note: if you want to add a new custom msg file and let the game function call it, you may need to edit the `GUIConfig.gcf` file (IDK if this is possible)  
 
# Usage
## Command Line Usage
print help for command line args usage:

```REMSG_Converter.exe -h```

## Convert msg to json / txt / csv
drag .msg.* file/folder to `msg2{csv/json/txt}.bat`

## Convert json / txt / csv to msg
drag .csv/.json/.txt file/folder **AND** .msg.* file/folder to `{csv/json/txt}+msg2msg.bat`

the `filename.msg.{version}.new` file is the modded file

## Use as python module
```py
# use case could be find at main.py. under DebugTest() or worker()
import REMSGUtil
msg = REMSGUtil.importMSG("abcd.msg.123456") # get MSG object as msg
REMSGUtil.exportMSG(msg, "efgh.msg.123456") # export as msg file
REMSGUtil.exportCSV(msg, "abcd.msg.123456") # export as csv file
```
# Credits
* wwylele's [mhrice](https://github.com/wwylele/mhrice), for file structure.
* ponaromixxx's [msg tool](https://zenhax.com/viewtopic.php?f=12&t=13337), for file structure.
