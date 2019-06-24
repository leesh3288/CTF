#!/usr/bin/env python
#Licence LGPL v2.1

#https://github.com/minetest/minetest/blob/944ffe9e532a3b2be686ef28c33313148760b1c9/doc/mapformat.txt
#http://www.tutorialspoint.com/sqlite/sqlite_bitwise_operators.htm
#http://stackoverflow.com/questions/1294619/does-sqlite-support-any-kind-of-ifcondition-statement-in-a-select

import sys #to get parameters
import sqlite3
import mt_block_parser
import re
import os.path
import pickle
from z3 import *

#It is possible to get X, Y, Z directly by SQLite!
#for row in sourcecursor.execute(" SELECT "+
#                                " CASE WHEN `X` < 2048 THEN `X` ELSE `X` - 4096 END AS X, "+
#                                " CASE WHEN `Y` < 2048 THEN `Y` ELSE `Y` - 4096 END AS Y, "+
#                                " CASE WHEN `Z` < 2048 THEN `Z` ELSE `Z` - 4096 END AS Z "+
#                                " FROM ("+"SELECT "+
#                                    " (`pos`) & 4095 AS X, "+
#                                    " ((`pos`) & 16773120)>>12 AS Y, "+
#                                    " ((`pos`) & 68702699520)>>24 AS Z "+
#                                    " FROM `blocks`"+
#                                ")"):

source = r'../map.sqlite'

#use compiled regular expression to filter blocks by block content. it is faster that checking "in array".
useful_block_evidence = re.compile(
#"default:cobble|"+"bones:bones|"+
"mesecon"
)

sourceconn = sqlite3.connect(source)
sourcecursorXZ = sourceconn.cursor()
sourcecursor = sourceconn.cursor()

#X and Z min and max to know image size
for rowMinMax in sourcecursorXZ.execute(" SELECT "+
                                " MIN( CASE WHEN `X` < 2048 THEN `X` ELSE `X` - 4096 END ) AS minX, "+
                                " MIN( CASE WHEN `Z` < 2048 THEN `Z` ELSE `Z` - 4096 END ) AS minZ, "+
                                " MAX( CASE WHEN `X` < 2048 THEN `X` ELSE `X` - 4096 END ) AS maxX, "+
                                " MAX( CASE WHEN `Z` < 2048 THEN `Z` ELSE `Z` - 4096 END ) AS maxZ "+
                                " FROM ("+"SELECT "+
                                    " (`pos`) & 4095 AS X, "+
                                    " ((`pos`) & 68702699520)>>24 AS Z "+
                                    " FROM `blocks`"+
                                ")"):
    minX = rowMinMax[0]
    minZ = rowMinMax[1]
    maxX = rowMinMax[2]
    maxZ = rowMinMax[3]
    width = maxZ - minZ
    height = maxX - minX

print(width, height)

if os.path.isfile('data.pickle'):
    print("data.pickle exists, loading...")
    with open('data.pickle', 'rb') as f:
        data = pickle.load(f)
    print("Load complete.")
else:
    print("data.pickle nonexistent, fallback to parsing.")
    data = [[None]*((height+1)*16) for _ in range((width+1)*16)]  # data[z][x]
    blockdict = {b'mesecons_walllever:wall_lever_off': 0,  # always towards +Z
    b'mesecons_lamp:lamp_off': 1,  # always from -Z
    b'mesecons_insulated:insulated_on': 2,
    b'mesecons_insulated:insulated_off': 2,  # param2 0: X (ofs 1), 3: Z (ofs 0)
    b'mesecons_extrawires:crossover_01': 4,
    b'mesecons_extrawires:crossover_10': 4,
    b'mesecons_extrawires:crossover_on': 4,
    b'mesecons_extrawires:crossover_off': 4,
    b'mesecons_extrawires:tjunction_on': 5,  # param2 0 = excl. +Z, 1 = excl. +X, 2 = excl. -Z, 3 = excl. -X
    b'mesecons_extrawires:tjunction_off': 5,
    b'mesecons_extrawires:corner_on': 9,  # param2 0 = -Z -X, 1 = -X +Z, 2 = +Z +X, 3 = +X -Z
    b'mesecons_extrawires:corner_off': 9,
    b'mesecons_gates:and_on': 13,
    b'mesecons_gates:and_off': 13,
    b'mesecons_gates:or_on': 14,
    b'mesecons_gates:or_off': 14,
    b'mesecons_gates:xor_on': 15,
    b'mesecons_gates:xor_off': 15,
    b'mesecons_gates:not_on': 16,
    b'mesecons_gates:not_off': 16}

    total_chunks = height * width
    parsed_chunks = 0
    print("Parsing block data...")
    #assuming that map is moustly flat limit Y coordinate
    for row in sourcecursor.execute(" SELECT "+
                                    " CASE WHEN `X` < 2048 THEN `X` ELSE `X` - 4096 END AS X, "+
                                    " CASE WHEN `Y` < 2048 THEN `Y` ELSE `Y` - 4096 END AS Y, "+
                                    " CASE WHEN `Z` < 2048 THEN `Z` ELSE `Z` - 4096 END AS Z, "+
                                    " `pos`, "+
                                    " `data` "+
                                    " FROM ("+"SELECT "+
                                        " `pos`, "+
                                        " (`pos`) & 4095 AS X, "+
                                        " ((`pos`) & 16773120)>>12 AS Y, "+
                                        " ((`pos`) & 68702699520)>>24 AS Z, "+
                                        " `data` "+
                                        " FROM `blocks`"+
                                    ")"+
                                    " WHERE Y == 0; "):
        block = mt_block_parser.MtBlockParser(row[4])
        if useful_block_evidence.search(str(block.nameIdMappingsRead)) != None:
            if row[0] - minX < 0 or width <= row[0] - minX or height - row[2] + minZ < 0 or height <= height - row[2] + minZ:
                print("Do not fit:", row[0], row[1], row[2])
            else:
                block.nodeDataParse()
                block.nameIdMappingsParse()
                chunk_blockdict = {k: blockdict[v] for k, v in block.nameIdMappings.items() if blockdict.get(v) is not None}
                for z in range(16):
                    for x in range(16):
                        blockmap = chunk_blockdict.get(block.arrayParam0[z*256 + 2*16 + x])
                        if blockmap == 5 or blockmap == 9:
                            blockmap += block.arrayParam2[z*256 + 2*16 + x]
                        elif blockmap == 2 and block.arrayParam2[z*256 + 2*16 + x] == 0:
                            blockmap += 1
                        data[row[2]*16 + z][row[0]*16 + x] = blockmap
        parsed_chunks += 1
        if parsed_chunks % 1000 == 0:
            print("Parsed {0:.2f}%".format(parsed_chunks * 100 / total_chunks))

    sourceconn.close()
    print("Parsing complete.")
    
    print("dumping to data.pickle...")
    with open('data.pickle', 'wb') as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    print("Dump complete.")

MAX_Z = 1938
MAX_X = -1
for i in range(MAX_Z):
    for j in range((height+1)*16-1, -1, -1):
        if data[i][j] is not None:
            MAX_X = max(MAX_X, j)
            break

print(MAX_Z, MAX_X)

assert(data[MAX_Z][1] == 1)  # LAMP

z = 1
for i in range(40):
    assert(data[z][i] == 0)  # 40 levers
for i in range(40, MAX_X + 1):
    assert(data[z][i] is None)  # and nothing else
z += 1

func_input = input

LEVER = BoolVector('lever', 40)
input = LEVER + [None]*(MAX_X + 1 - 40)  # prev layer's output

S = Solver()
LAMP = None
while LAMP is None:
    print("Processing Z = {} / {}".format(z, MAX_Z))
    
    """
                output[x]
    layer[x-1] data[z][x] layer[x]
                input[x]
    """
    
    layer = [None]*MAX_X
    output = [None]*(MAX_X + 1)  # next layer's input
    
    # 1. create BoolVector for blocks in current layer
    for x in range(MAX_X):
        if data[z][x] is not None or data[z][x+1] is not None:
            layer[x] = Bool('l{}_{}'.format(z, x))
    for x in range(MAX_X + 1):
        if data[z][x] is not None:
            output[x] = Bool('o{}_{}'.format(z, x))
    
    # 2. put appropriate restrictions on current layer, connecting input & output
    for x in range(MAX_X + 1):
        if data[z][x] is not None:
            b = data[z][x]
            if b == 1:
                LAMP = input[x]
                break
            elif b == 2:
                S.add(output[x] == input[x])
            elif b == 3:
                S.add(layer[x-1] == layer[x])
            elif b == 4:
                S.add(output[x] == input[x])
                S.add(layer[x-1] == layer[x])
            elif b == 5:
                assert(False)
            elif b == 6:
                S.add(output[x] == layer[x-1])
                S.add(layer[x-1] == input[x])
            elif b == 7:
                assert(False)
            elif b == 8:
                S.add(output[x] == layer[x])
                S.add(layer[x] == input[x])
            elif b == 9:
                S.add(layer[x-1] == input[x])
            elif b == 10:
                S.add(output[x] == layer[x-1])
            elif b == 11:
                S.add(output[x] == layer[x])
            elif b == 12:
                S.add(layer[x] == input[x])
            elif b == 13:
                S.add(output[x] == And(layer[x-1], layer[x]))
            elif b == 14:
                S.add(output[x] == Or(layer[x-1], layer[x]))
            elif b == 15:
                S.add(output[x] == Xor(layer[x-1], layer[x]))
            elif b == 16:
                S.add(output[x] == Not(input[x]))
    
    # 4. set output layer as input layer, increment z
    input = output
    z += 1

# add final condition
S.add(LAMP == True)

print(LAMP)

print(S.check())
m = S.model()
print([m[LEVER[i]] for i in range(40)])