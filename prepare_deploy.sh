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
rm -rf  ./pyodin/logs/*
#
mkdir "$DEPLOY_DIR"
#
cp -aR client/app "$DEPLOY_DIR"
cp -aR install "$DEPLOY_DIR"
cp -aR pyodin "$DEPLOY_DIR"
cp -aR server "$DEPLOY_DIR"

rm -rf "$DEPLOY_DIR/pyodin/logs/*"
rm -rf "$DEPLOY_DIR/pyodin/conf/*.conf"
rm -rf "$DEPLOY_DIR/pyodin/test"

mkdir "$DEPLOY_DIR/docs"
cp -aR README.pdf "$DEPLOY_DIR/docs"

find ${DEPLOY_DIR} -name CVS -prune -exec rm -rf {} \;
find ${DEPLOY_DIR} -name .svn -prune -exec rm -rf {} \;
find ${DEPLOY_DIR} -name .pyc -prune -exec rm -rf {} \;

DEPLOY_FILE_NAME="odin_${VER_MAJOR}_${VER_MINOR}_${VER_PATCH}_${VER_FLAG}".tar.gz
tar cvzf "$DEPLOY_FILE_NAME" "$DEPLOY_DIR"

if [ ! -f "$DEPLOY_FILE_NAME" ]; then
    echo "Deploy build failed."
    rm -rf "$DEPLOY_DIR"
    exit 1
fi


rm -rf "$DEPLOY_DIR"
echo "Deploy build complete."
