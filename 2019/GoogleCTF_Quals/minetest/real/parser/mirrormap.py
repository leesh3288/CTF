#!/usr/bin/env python
#Licence LGPL v2.1

#mirror map. just for fun and to prove concept of block reassembling.

import sys #to get parameters
import sqlite3
import cStringIO
import time
import mt_block_parser


def rposAsInt(p):
    return int(p[2]*16*16 + p[1]*16 + p[0])

def intAsRpos(i):
    x = i % 16
    i = int((i - x) / 16)
    y = i % 16
    i = int((i - y) / 16)
    z = i % 16
    return x,y,z

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

# Convert location to integer
def getBlockAsInteger(p):
	return int64(p[2]*16777216 + p[1]*4096 + p[0])
def int64(u):
	while u >= 2**63:
		u -= 2**64
	while u <= -2**63:
		u += 2**64
	return u

source = r'<Put your path to world folder here>/map.sqlite.backup'
target = r'<Put your path to world folder here>/map.sqlite.clear'
arguments = sys.argv
if(len(arguments) == 3 ):
    source = str(arguments[1])
    target = str(arguments[2])


sourceconn = sqlite3.connect(source)
targetconn = sqlite3.connect(target)
sourcecursor0 = sourceconn.cursor()
sourcecursor = sourceconn.cursor()
targetcursor = targetconn.cursor()

targetcursor.execute("CREATE TABLE IF NOT EXISTS `blocks` (`pos` INT NOT NULL PRIMARY KEY, `data` BLOB);")

m = {} #mirrored order of keys
for i in range(0, 4096):
    p = intAsRpos(i)
    m[i] = rposAsInt([p[0], p[1], 15-p[2]])
    
facedir_nodelist = ['default:chest', 'default:chest_locked', 'default:bookshelf', 
'door_wood_a', 'door_wood_b', 'door_steel_a', 'door_steel_b',  #doors are more complicated, TODO
'default:furnace', 'default:furnace_active',
'beds:fancy_bed_top', 'beds:fancy_bed_bottom', 'beds:bed_top', 'beds:bed_bottom']

for row in sourcecursor0.execute("SELECT `pos` FROM `blocks`"):
    pos=getIntegerAsBlock(row[0])
    if pos[0]**2 + pos[2]**2 < (160/16)**2 and pos[1]>(-60/16) and pos[1]<(128/16):    #just small central map part for fast demonstration
        for datarow in sourcecursor.execute("SELECT `data` FROM `blocks` WHERE `pos` == ? LIMIT 1;", (row[0],)):
            tempA = mt_block_parser.MtBlockParser(datarow[0])
            tempA.nodeDataParse()
            tempA.nodeMetadataParse()
            tempA.nameIdMappingsParse()
            
            tempB = mt_block_parser.MtBlockParser(0) #blank block
            
            for i in range(0, 4096):
                tempB.arrayParam0[i] = tempA.arrayParam0[m[i]]
                tempB.arrayParam1[i] = tempA.arrayParam1[m[i]]
                tempB.arrayParam2[i] = tempA.arrayParam2[m[i]]
                if tempA.arrayParam0[i] not in tempB.nameIdMappings:
                    tempB.nameIdMappings[tempA.arrayParam0[i]] = tempA.nameIdMappings[tempA.arrayParam0[i]]
                if m[i] in tempA.arrayMetadataRead:
                    tempB.arrayMetadataRead[i] = tempA.arrayMetadataRead[m[i]]
                    tempB.arrayMetadataReadInventory[i] = tempA.arrayMetadataReadInventory[m[i]]
                #rotate nodes wallmounted
                if tempA.arrayParam2[m[i]] == 4:
                    tempB.arrayParam2[i] = 5
                elif tempA.arrayParam2[m[i]] == 5:
                    tempB.arrayParam2[i] = 4
                #rotate nodes facedir
                elif tempA.arrayParam2[m[i]] == 0:
                    if tempA.nameIdMappings[tempA.arrayParam0[m[i]]] in facedir_nodelist:
                        tempB.arrayParam2[i] = 2
                elif tempA.arrayParam2[m[i]] == 2:
                    if tempA.nameIdMappings[tempA.arrayParam0[m[i]]] in facedir_nodelist:
                        tempB.arrayParam2[i] = 0
            
            tempB.nodeDataCompile()
            tempB.nodeMetadataCompile()
            tempB.nameIdMappingsCompile()
            
            cleared_block = sqlite3.Binary(tempB.selfCompile())
            
            posm = [pos[0], pos[1], -pos[2]]
            targetcursor.execute("INSERT OR IGNORE INTO `blocks` VALUES (?, ?);", (getBlockAsInteger(posm), cleared_block))
            if pos[0] == 0 and pos[2] == 0:
                targetconn.commit()
                print row[0]    #at least something to see progress

targetconn.commit()
sourceconn.close()
targetconn.close()

