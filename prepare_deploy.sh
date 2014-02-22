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
mkdir "$DEPLOY_DIR/app"
cp -aR client/app "$DEPLOY_DIR/app"
cp -aR install "$DEPLOY_DIR"
cp -aR pyodin "$DEPLOY_DIR"
cp -aR server "$DEPLOY_DIR"

DEPLOY_FILE_NAME="odin_${VER_MAJOR}_${VER_MINOR}_${VER_PATCH}_${VER_FLAG}".tar.gz
tar cvzf "$DEPLOY_FILE_NAME" "$DEPLOY_DIR"

if [ ! -f "$DEPLOY_FILE_NAME" ]; then
    echo "Deploy build failed."
    exit 1
fi


rm -rf "$DEPLOY_DIR"
echo "Deploy build complete."
