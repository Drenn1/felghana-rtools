# Add 0.15s of silence to the start and end of the audio files to fix audio
# being cut off. The english audio files do this already, so it may be
# a PC-exclusive quirk.
#
# Unfortunately this re-encodes the audio. I couldn't find a way to avoid it.
# Also this script doesn't work with spaces in folder names.

sourceDir=$1
targetDir=$2

fileList=$(find "$sourceDir" -name '*.ogg') 

for f in $fileList; do
    src=$f
    dest=$(echo $f | sed "s\$$sourceDir\$$targetDir\$")
    echo "$src" "->" "$dest"
    ffmpeg -y -f lavfi -t 0.15 -i anullsrc=channel_layout=stereo:sample_rate=44100 -i $src -filter_complex "[0:a][1:a][0:a]concat=n=3:v=0:a=1" -aq 10 $dest 2>/dev/null
done
