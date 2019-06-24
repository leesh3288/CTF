#!/usr/bin/env python
#Licence LGPL v2.1

#Copy all blocks, but remove from them all objects.

import sys #to get parameters
import sqlite3
import mt_block_parser

import struct
import zlib

source = r'<Put your path to world folder here>/map.sqlite.backup'
target = r'<Put your path to world folder here>/map.sqlite.clear'
arguments = sys.argv
if(len(arguments) == 3 ):
    source = str(arguments[1])
    target = str(arguments[2])

sourceconn = sqlite3.connect(source)
targetconn = sqlite3.connect(target)
sourcecursor = sourceconn.cursor()
targetcursor = targetconn.cursor()
targetcursor.execute("CREATE TABLE IF NOT EXISTS `blocks` (`pos` INT NOT NULL PRIMARY KEY, `data` BLOB);")

for row in sourcecursor.execute("SELECT `pos`, `data` "+" FROM `blocks`;"):
    block = mt_block_parser.MtBlockParser(row[1])
    if block.static_object_count == 0:
        targetcursor.execute("INSERT OR IGNORE INTO `blocks` VALUES (?, ?);", (row[0], row[1]))
    else:
        #combine block back to string, but leave objects out
        block.objectsRead = struct.pack('>H', 0)
        cleared_block = block.selfCompile()
        targetcursor.execute("INSERT OR IGNORE INTO `blocks` VALUES (?, ?);", (row[0], sqlite3.Binary(cleared_block)))
            
targetconn.commit()

sourceconn.close()
targetconn.close()
