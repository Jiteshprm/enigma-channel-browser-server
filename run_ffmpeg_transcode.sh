#!/bin/bash

killall -9 ffmpeg

#Transcoding Channel: aaa
ffmpeg -hwaccel cuvid -c:v h264_cuvid -vsync 0 -hwaccel cuvid -i http://192.168.0.37:8001/1:0:19:51A3:C8B:3:EB0000:0:0:0: -vcodec h264_nvenc -ar 44100 -c:a libfdk_aac -g 20 -b:v 1000k -f flv rtmp://127.0.0.1:8081/hls/live &