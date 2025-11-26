#/bin/env bash

PICS_DIR=~/test_pics 		# Replace to your temp directory
VIDEO_DEVICE=/dev/video0 	# Replace to your camera device

echo Capture from $VIDEO_DEVICE to $PICS_DIR

ffmpeg -f v4l2 -i $VIDEO_DEVICE -q:v 20 -vf fps=1.5 $PICS_DIR/out_%08d.jpg
