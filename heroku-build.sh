#!/bin/bash
# Script to build the React frontend for Heroku deployment

echo "===== Building React frontend ====="
cd frontend
npm install
npm run build

echo "===== Listing React build directory contents ====="
ls -la build/
ls -la build/static/js/
ls -la build/static/css/

echo "===== Creating staticfiles directory ====="
cd ..
mkdir -p staticfiles

echo "===== Copying React build files to staticfiles ====="
cp -rv frontend/build/* staticfiles/

echo "===== Listing staticfiles directory contents ====="
ls -la staticfiles/
ls -la staticfiles/static/js/ || echo "No js directory found in staticfiles/static"
ls -la staticfiles/static/css/ || echo "No css directory found in staticfiles/static"

echo "===== Build process completed successfully! ====="
