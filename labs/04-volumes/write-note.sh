#!/bin/sh
# 在容器里往 /data/note.txt 追加一行，然后打印文件内容。
# 本脚本会被挂进容器使用，见 README。
set -eu
mkdir -p /data
echo "$(date) written-inside-container" >> /data/note.txt
echo "----- /data/note.txt -----"
cat /data/note.txt
