#!/bin/bash

killall -9 ffmpeg

#Transcoding Channel: RTP 1
ffmpeg -hwaccel cuvid -c:v h264_cuvid -vsync 0 -hwaccel cuvid -i http://192.168.0.37:8001/1:0:1:65:65:53:CE40000:0:0:0: -vcodec h264_nvenc -ar 44100 -c:a libfdk_aac -g 20 -b:v 1000k -f flv rtmp://127.0.0.1:8081/hls/live &