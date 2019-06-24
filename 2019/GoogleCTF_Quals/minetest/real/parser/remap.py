#!/usr/bin/env python

#Licence LGPL v2.1
#Creates copy of map db, leaving only specified(filtered) blocks.
#Can also be used for map backup, may-be even online backup.

import sys #to get parameters
import sqlite3
import mt_block_parser

import re

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

#use compiled regular expression to filter blocks by block content. it is faster that checking "in array".
useful_block_evidence = re.compile(
    "default:cobble|"+
    "protector:protect|default:chest_locked|doors:door_steel|"+
    "default:chest|default:torch|default:stonebrick|default:glass|default:obsidian_glass|"+
    "default:ladder|default:rail|default:fence_wood|"+
    "bones:bones"
    )

sourceconn = sqlite3.connect(source)
targetconn = sqlite3.connect(target)
sourcecursor = sourceconn.cursor()
targetcursor = targetconn.cursor()
targetcursor.execute("CREATE TABLE IF NOT EXISTS `blocks` (`pos` INT NOT NULL PRIMARY KEY, `data` BLOB);")

for row in sourcecursor.execute("SELECT `pos`, `data` "+" FROM `blocks`;"):
    pos=getIntegerAsBlock(row[0])
    if pos[0]**2 + pos[2]**2 < (160/16)**2 and pos[1]>(-60/16):    #160 nodes radius and 60 nodes deep
        targetcursor.execute("INSERT OR IGNORE INTO `blocks` VALUES (?, ?);", (row[0], row[1]))
    else:
        try:
            temp = mt_block_parser.MtBlockParser(row[1])
            if useful_block_evidence.search(temp.nameIdMappingsRead)!=None:
                targetcursor.execute("INSERT OR IGNORE INTO `blocks` VALUES (?, ?);", (row[0], row[1]))
        except:
            print "Block parse error:", pos[0], pos[1], pos[2]
            
targetconn.commit()

sourceconn.close()
targetconn.close()
