echo "Downloading Playlist at: $1"
youtube-dl --yes-playlist -f 'worst[height>=480][height<=720][vcodec*=avc1]/best[height<=480][vcodec*=avc1]' -o '~/Videos/Youtube/%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s' $1
