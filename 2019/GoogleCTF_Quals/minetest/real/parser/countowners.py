#!/usr/bin/env python
#Licence LGPL v2.1

#list owners of protection blocks and locked chests

import sys #to get parameters
import sqlite3
import operator
import mt_block_parser
import re


source = r'<Put your path to world folder here>/map.sqlite.backup'
target = r'<Put path to output text file>'
arguments = sys.argv
if(len(arguments) > 1 ):
    source = str(arguments[1])
if(len(arguments) > 2 ):
    target = str(arguments[2])

print source

sourceconn = sqlite3.connect(source)
sourcecursor = sourceconn.cursor()

#ownprot = {}
ownchest = {}
ownsomething = {}

#owned_block_evidence = re.compile("protector:protect")
#owned_block_evidence = re.compile("default:chest_locked")
owned_block_evidence = re.compile("protector:protect|protector_mese:protect|default:chest_locked")



for datarow in sourcecursor.execute("SELECT `data` FROM `blocks`"):
    temp = mt_block_parser.MtBlockParser(datarow[0])
    if owned_block_evidence.search(temp.nameIdMappingsRead)!=None:
        temp.nodeDataParse()
        temp.nodeMetadataParse()
        temp.nameIdMappingsParse()
        for i in range(0, 4096):
            tempName = temp.nameIdMappings[temp.arrayParam0[i]]
#                if tempName == 'protector:protect':
#                    if temp.arrayMetadataRead[i]['owner'] in ownprot:
#                        ownprot[temp.arrayMetadataRead[i]['owner']]+= 1
#                    else:
#                        ownprot[temp.arrayMetadataRead[i]['owner']] = 1
#                if tempName == 'default:chest_locked':
#                    if temp.arrayMetadataRead[i]['owner'] in ownchest:
#                        ownchest[temp.arrayMetadataRead[i]['owner']]+= 1
#                    else:
#                        ownchest[temp.arrayMetadataRead[i]['owner']] = 1
            if tempName == 'protector:protect' or tempName == 'protector_mese:protect' or tempName == 'default:chest_locked':
                if temp.arrayMetadataRead[i]['owner'] in ownsomething:
                    ownsomething[temp.arrayMetadataRead[i]['owner']]+= 1
                else:
                    ownsomething[temp.arrayMetadataRead[i]['owner']] = 1
                    
#s_ownprot = sorted(ownprot.items(), key=operator.itemgetter(1))
#s_ownchest = sorted(ownchest.items(), key=operator.itemgetter(1))
s_ownsomething = sorted(ownsomething.items(), key=operator.itemgetter(1))

with open(target, "w") as text_file:
    for n in s_ownsomething:
        text_file.write(str(n[0]) + "\n")
        print n

#datafile = file('auth.txt')
#for line in datafile:
#    for i,n in enumerate(s_ownprot):
#        pname = line.split(':')[0]
#        if pname == n[0]:
#            s_ownprot[i] = (n[0], line)
#
#with open("auth_re.txt", "w") as text_file:
#    for n in s_ownprot:
#        if isinstance(n[1], basestring):
#            text_file.write(n[1])
#        else:
#            print n

sourceconn.close()

