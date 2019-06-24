map_unexplore
=============

Scripts for Minetest game map v25 format.

mt_block_parser.py - Can do partial or full parsing of map block. Can reassemble("Compile") block back to binary data.


remap.py - Decrease minetest map size and saves it as backup(most likely even online).

domap.py - Creates simple image, to show where player hawe built something.

clrmap.py - Clears all objects from map and saves it as backup.

mt_block_parser.py - Can be used to read map block data from your code.

recover.py - Copy only helthy map blocks.

mirrormap.py - Creates mirrored version of map.

countowners.py - Get a list with players, who own protected chests and number of chests.

inspectmap.py - Get list of names for all nodes present on the map.

Now can pass paths to database files. Use like "./script.py &lt;source.sqlite&gt; &lt;target.sqlite&gt;" (or "&lt;pythonpath&gt;\python.exe script.py &lt;source.sqlite&gt; &lt;target.sqlite&gt;" on Windows)
