#!/bin/sh

set -e

REMOTE_HOST="ix"
REMOTE_BASE_DIR="/research/paraducks/tauwww"
REMOTE_RELEASES_DIR="$REMOTE_BASE_DIR/doc-releases"
SYMLINK_NAME="current"
LOCAL_BUILD_DIR="./build"
NUM_RELEASES_TO_KEEP=5

RELEASE_NAME=$(date +"%Y-%b-%d_%H-%M-%S")
FULL_REMOTE_RELEASE_PATH="$REMOTE_RELEASES_DIR/$RELEASE_NAME"

echo "Preparing remote release directory: $FULL_REMOTE_RELEASE_PATH"
ssh "$REMOTE_HOST" "mkdir -p $FULL_REMOTE_RELEASE_PATH"

echo "Uploading docs to: $FULL_REMOTE_RELEASE_PATH"
rsync -avz "$LOCAL_BUILD_DIR/html-docs/" "$REMOTE_HOST:$FULL_REMOTE_RELEASE_PATH/html-docs/"
rsync -avz "$LOCAL_BUILD_DIR/pdf/" "$REMOTE_HOST:$FULL_REMOTE_RELEASE_PATH/"

echo "Activating new release by pointing '$SYMLINK_NAME' to '$RELEASE_NAME'..."
ssh "$REMOTE_HOST" "cd $REMOTE_RELEASES_DIR; ln -sfn $RELEASE_NAME $SYMLINK_NAME"

echo "Cleaning up old remote releases..."
DELETE_COUNT=$(($NUM_RELEASES_TO_KEEP + 1))
ssh "$REMOTE_HOST" "cd $REMOTE_RELEASES_DIR; ls -1dt . | grep -v \"^$SYMLINK_NAME$\" | tail -n +$DELETE_COUNT | xargs -r rm -rf"

echo "---------------------------------------------------------"
echo "'$SYMLINK_NAME' release is now: $RELEASE_NAME"
echo "---------------------------------------------------------"

  