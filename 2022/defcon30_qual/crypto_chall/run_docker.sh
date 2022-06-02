#!/bin/bash
docker rm -f cryptochall
docker run --cap-add SYS_PTRACE --security-opt apparmor:unconfined -it -d -p65400:65400 --name cryptochall cryptochall