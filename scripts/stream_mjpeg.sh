#/bin/env bash

TARGET_EP='_your_jpeg_tcp_listener_url_'
VIDEO_DEVICE=/dev/video0					# Replace to your camera device

FPS=6

echo Stream MJPEG to $TARGET_EP

ffmpeg -f v4l2 -i $VIDEO_DEVICE -q:v 24 -vf fps=$FPS -f mjpeg tcp://$TARGET_EP
