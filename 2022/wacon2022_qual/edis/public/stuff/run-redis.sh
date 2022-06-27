#!/bin/sh
exec 0>&-
exec 1>&-
exec 2>&-

tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
modulePath=$PWD/decoder.so
cd $tmp_dir;
timeout 60 redis-server --port $1 --loadmodule $modulePath;
cd /;
rm -rf $tmp_dir
