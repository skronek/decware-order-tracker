#!/bin/bash
# Build the React frontend for Heroku and hand it to Django.
set -euo pipefail
cd "$(dirname "$0")"

(cd frontend && npm ci && npm run build)

mkdir -p staticfiles decware_order_tracker/templates/react
cp -r frontend/build/* staticfiles/
cp frontend/build/index.html decware_order_tracker/templates/react/index.html
