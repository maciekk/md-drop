#!/usr/bin/env bash
set -e

# Your permanent deployment ID — find it with: clasp deployments
# Set once; never changes. The URL stays stable across all future deploys.
DEPLOYMENT_ID="${CLASP_DEPLOYMENT_ID:-}"

if [ -z "$DEPLOYMENT_ID" ]; then
  echo "Error: set CLASP_DEPLOYMENT_ID in your environment (or hardcode it below)."
  echo "Find it with: clasp deployments"
  exit 1
fi

VERSION=$(date "+%Y-%m-%d %H:%M")
sed -i "s/^var VERSION = .*/var VERSION = \"$VERSION\";/" Code.gs
echo "VERSION set to: $VERSION"

clasp push
clasp deploy --deploymentId "$DEPLOYMENT_ID" --description "md-drop $VERSION"
echo "Deployed to existing deployment — URL unchanged."
