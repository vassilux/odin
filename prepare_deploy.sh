#!/bin/bash
#
# 
# Description : Prepare deploy packages for odin application. 
# Author : vassilux
# Last modified : 2014-02-20 14:37:47 
#

set -e
DEPLOY_DIR="odin"

VER_MAJOR="1"
VER_MINOR="0"
VER_PATCH="0"

if [ -d "$DEPLOY_DIR" ]; then
    rm -rf  "$DEPLOY_DIR"
fi
#
mkdir "$DEPLOY_DIR"
#
cp -aR client/app "$DEPLOY_DIR"
cp -aR install "$DEPLOY_DIR"
cp -aR pyodin "$DEPLOY_DIR"
cp -aR server "$DEPLOY_DIR"

rm -rf "$DEPLOY_DIR/pyodin/logs/*.log"
rm -rf "$DEPLOY_DIR/pyodin/conf/odinami.conf"
rm -rf "$DEPLOY_DIR/pyodin/conf/odinamilogger.conf"
rm -rf "$DEPLOY_DIR/pyodin/conf/odinf1com.conf"
rm -rf "$DEPLOY_DIR/pyodin/conf/odinincall.conf"
rm -rf "$DEPLOY_DIR/pyodin/conf/odinsys.conf"
rm -rf "$DEPLOY_DIR/pyodin/conf/odinsyslogger.conf"
rm -rf "$DEPLOY_DIR/pyodin/test"

rm -rf "$DEPLOY_DIR/server/test"
rm -rf "$DEPLOY_DIR/server/logs/*.log"
rm -rf "$DEPLOY_DIR/server/config/config.json"
rm -rf "$DEPLOY_DIR/server/config.js"
rm -rf "$DEPLOY_DIR/server/.gitignore"
rm -rf "$DEPLOY_DIR/server/.travis.yml"
rm -rf "$DEPLOY_DIR/server/gruntFile.js"
rm -rf "$DEPLOY_DIR/server/generatePackages.js"
rm -rf "$DEPLOY_DIR/server/Makefile"
rm -rf "$DEPLOY_DIR/server/TODO.txt"

mkdir "$DEPLOY_DIR/docs"
cp -aR README.pdf "$DEPLOY_DIR/docs"

find ${DEPLOY_DIR}/* -name CVS -prune -exec rm -rf {} \;
find ${DEPLOY_DIR}/* -name .svn -prune -exec rm -rf {} \;
find ${DEPLOY_DIR}/* -name .pyc -prune -exec rm -rf {} \;

DEPLOY_FILE_NAME="odin_${VER_MAJOR}_${VER_MINOR}_${VER_PATCH}_${VER_FLAG}".tar.gz
tar cvzf "$DEPLOY_FILE_NAME" "$DEPLOY_DIR"

if [ ! -f "$DEPLOY_FILE_NAME" ]; then
    echo "Deploy build failed."
    rm -rf "$DEPLOY_DIR"
    exit 1
fi


rm -rf "$DEPLOY_DIR"
echo "Deploy build complete."
