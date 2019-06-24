#!/usr/bin/env python
#Licence LGPL v2.1

#Find what nodes map contains

import sys #to get parameters
import sqlite3
import operator
import mt_block_parser


source = r'<Put your path to world folder here>/map.sqlite.backup'
target = r'<Put path to output text file>'
arguments = sys.argv
if(len(arguments) > 1 ):
    source = str(arguments[1])
if(len(arguments) > 2 ):
    target = str(arguments[2])

sourceconn = sqlite3.connect(source)
sourcecursor0 = sourceconn.cursor()
sourcecursor = sourceconn.cursor()

nodelist = {}

for row in sourcecursor0.execute("SELECT `pos` FROM `blocks`"):
    for datarow in sourcecursor.execute("SELECT `data` FROM `blocks` WHERE `pos` == ? LIMIT 1;", (row[0],)):
        temp = mt_block_parser.MtBlockParser(datarow[0])

        temp.nameIdMappingsParse()
        for key,value in temp.nameIdMappings.iteritems():
            if value not in nodelist:
                nodelist[value] = 0

        #Counting all nodes takes too long
        # temp.nodeDataParse()
        # for i in range(0, 4096):
        #     tempName = temp.nameIdMappings[temp.arrayParam0[i]]
        #     nodelist[tempName]+= 1

s_nodelist = sorted(nodelist)
#s_nodelist = sorted(nodelist.items(), key=operator.itemgetter(1))

with open(target, "w") as text_file:
    for n in s_nodelist:
        text_file.write(str(n) + "\n")
        #text_file.write(str(n[0]) + ' ' + str(n[1]) + "\n")
        print n

sourceconn.close()
