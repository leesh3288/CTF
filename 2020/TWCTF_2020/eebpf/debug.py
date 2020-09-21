import os

r = os.system("gcc main.c -o exploit -static")
if r == 0:
    os.system("""
    mkdir -p mount;
    cd mount;
    cpio -idv < ../debugfs.cpio 2> /dev/null;
    cp ../exploit .
    find -print0 | cpio -o --null --format=newc > ../debugfs.cpio;
    """)
    os.system("./run.sh")
