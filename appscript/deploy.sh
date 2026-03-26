#!/usr/bin/env bash
set -e

VERSION=$(date "+%Y-%m-%d %H:%M")
sed -i "s/^var VERSION = .*/var VERSION = \"$VERSION\";/" Code.gs
echo "VERSION set to: $VERSION"

clasp push
