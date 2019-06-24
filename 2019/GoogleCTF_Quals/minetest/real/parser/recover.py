#!/usr/bin/env python
#Licence LGPL v2.1

#Copy all blocks except corrupted ones

import sys #to get parameters
import sqlite3
import mt_block_parser

import struct
import zlib

def getIntegerAsBlock(i):
    x = unsignedToSigned(i % 4096, 2048)
    i = int((i - x) / 4096)
    y = unsignedToSigned(i % 4096, 2048)
    i = int((i - y) / 4096)
    z = unsignedToSigned(i % 4096, 2048)
    return x,y,z
def unsignedToSigned(i, max_positive):
    if i < max_positive:
        return i
    else:
        return i - 2*max_positive

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
    pos=getIntegerAsBlock(row[0])
    try:
        temp = mt_block_parser.MtBlockParser(row[1])
        if temp:
            targetcursor.execute("INSERT OR IGNORE INTO `blocks` VALUES (?, ?);", (row[0], row[1]))
    except:
        print "Block parse error:", pos[0], pos[1], pos[2]
            
targetconn.commit()

sourceconn.close()
targetconn.close()
