#!/bin/sh
# Render the make.fun post-x video: "The agent builds a game from one prompt".
#
# Creative, in my own words: one prompt on screen, typed out like a chat
# message — "build me a tiny browser game: a neon snake game" — then the
# agent visibly working in a terminal, files landing as they are written,
# then the finished game actually running: real gameplay captured from a
# headless browser, the snake eating and the score climbing. The video ends
# on make.fun's own referral end card, fetched fresh from the press-pack
# manifest, with Rex's referral code typed into its field.
#
# Structure (28 s, 1080x1920, 30 fps):
#   0.0-4.0    the prompt, typed into a chat frame (PIL frames)
#   4.0-12.0   the agent working: terminal + files appearing (PIL frames)
#   12.0-25.5  real gameplay capture, headless Chromium, scripted play
#   25.5-28.0  make.fun referral end card over blurred gameplay, code typed in
#
# Inputs (all inside this repo):
#   scripts/frames/a_*.png, b_*.png   PIL-rendered frames (make_frames.py)
#   scripts/gameplay/*.webm           real gameplay capture (capture_gameplay.py)
#   assets/press/makefun-card-9x16-transparent.webm   end card, fetched fresh
#   assets/fonts/JetBrainsMono-Bold.ttf referral code typeface
#
# Outputs (in the repo root): music.wav (generated bed), video.mp4.
# Run from the repo root:  sh scripts/render.sh
set -e
cd "$(dirname "$0")/.."

CODE=17s3abg9
DUR=28
CARD_START=25.5
CARD_LEN=2.5
CARD_REST=1.433
CODE_T=$(python3 -c "print(25.5+1.433)")
MONO=assets/fonts/JetBrainsMono-Bold.ttf
GAMEPLAY=$(ls scripts/gameplay/*.webm | head -n 1)

# --- 1. Music bed: a 120 BPM synth pulse, generated, nothing copyrighted.
# A kick thump each half second, a bass line cycling A-F-C-G each second,
# and a bright pluck arpeggio every quarter second, all from sine waves.
ffmpeg -v error -y -f lavfi -i \
  "aevalsrc='0.55*sin(2*PI*110*t)*exp(-10*mod(t,0.5))+0.30*sin(2*PI*(110*eq(floor(mod(t,4)),0)+87.31*eq(floor(mod(t,4)),1)+130.81*eq(floor(mod(t,4)),2)+98*eq(floor(mod(t,4)),3))*t)*(0.7+0.3*sin(2*PI*2*t))+0.12*sin(2*PI*(440*eq(floor(mod(t,1)/0.25),0)+523.25*eq(floor(mod(t,1)/0.25),1)+659.25*eq(floor(mod(t,1)/0.25),2)+880*eq(floor(mod(t,1)/0.25),3))*t)*exp(-5*mod(t,0.25))':s=48000:d=$DUR" \
  -af "lowpass=f=4000,volume=0.9,afade=t=in:st=0:d=0.1,afade=t=out:st=27:d=1" \
  -c:a pcm_s16le music.wav

# --- 2. Assemble the 28 s video.
# Frames a (0-4s) + frames b (4-12s) + gameplay (12-25.5s, blurred-fill
# background with the game centred) + the referral end card over the last
# 2.5 s, the clip blurring and losing saturation under it, and the referral
# code typed into the field once the field has come to rest (1.433 s into
# the card). The caret is covered with white first so it does not blink
# beside the code.
ffmpeg -v error -y \
  -framerate 30 -i scripts/frames/a_%04d.png \
  -framerate 30 -i scripts/frames/b_%04d.png \
  -i "$GAMEPLAY" \
  -c:v libvpx-vp9 -i assets/press/makefun-card-9x16-transparent.webm \
  -i music.wav \
  -filter_complex "\
[0:v]fps=30,format=yuv420p,trim=0:4,setpts=PTS-STARTPTS[segA];\
[1:v]fps=30,format=yuv420p,trim=0:8,setpts=PTS-STARTPTS[segB];\
[2:v]trim=0.5:14.0,setpts=PTS-STARTPTS,fps=30,format=yuv420p,split[gp][gpsoft];\
[gpsoft]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg];\
[gp]scale=1080:-1[fg];\
[bg][fg]overlay=(W-w)/2:(H-h)/2,trim=0:13.5,setpts=PTS-STARTPTS[game];\
[segA][segB][game]concat=n=3:v=1:a=0,tpad=stop_mode=clone:stop_duration=2.5,split[clip][soft];\
[soft]gblur=sigma=28,eq=saturation=0.35,fade=t=in:st=$CARD_START:d=0.8:alpha=1[soft];\
[clip][soft]overlay[bg2];\
[3:v]format=yuva420p,setpts=PTS-STARTPTS+$CARD_START/TB[card];\
[bg2][card]overlay=eof_action=pass,drawbox=x=208:y=1230:w=9:h=82:color=white:t=fill:enable='gte(t,$CODE_T)',drawtext=fontfile=$MONO:text=$CODE:fontsize=62:fontcolor=0x191419:x=210:y=1271-(ascent-descent)/2:enable='gte(t,$CODE_T)'[v]" \
  -map "[v]" -map "4:a" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium \
  -c:a aac -b:a 128k -t $DUR -movflags +faststart video.mp4

ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate,codec_name -of default=noprint_wrappers=1 video.mp4
ls -la video.mp4
