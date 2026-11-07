#!/bin/bash

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

echo "SCRIPT_DIR: $SCRIPT_DIR"

cd "$SCRIPT_DIR"

brew install p7zip

7z x nonoha-engine.7z
