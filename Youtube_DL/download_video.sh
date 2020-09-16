echo "Downloading video for url: $1"
youtube-dl --no-playlist -f 'worst[height>=480][height<=720][vcodec*=avc1]/best[height<=480][vcodec*=avc1]' -o '~/Videos/Youtube/%(uploader)s/No Playlist/%(title)s.%(ext)s' $1
