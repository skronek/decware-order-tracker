#!/bin/bash
# Script to build the React frontend for Heroku deployment

echo "Building React frontend..."
cd frontend
npm install
npm run build

echo "Creating staticfiles directory..."
cd ..
mkdir -p staticfiles

echo "Copying build files to staticfiles..."
cp -r frontend/build/* staticfiles/

echo "Build process completed successfully!"
