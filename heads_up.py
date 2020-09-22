#!/usr/bin/python3
from menu_util import Menu, FileBrowserMenu, Directory, Option
import os, re, time
from ffprobe import FFProbe
from GiantBomb_DL.giantbomb_dl import GiantBombMenu

VIDEO_ROOT = "/home/pi/Videos"
PLAY_VIDEO_COMMAND_FORMAT = "omxplayer -o alsa {}"
RESUME_VIDEO_COMMAND_FORMAT = "omxplayer -o alsa --pos {} {}"
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mkv", ".avi"]
VIDEO_METADATA_FORMAT = "humd"

MAIN_HEADER = "Select a Function"
WATCH_VIDEOS_HEADER = "Watch Videos"
DOWNLOAD_VIDEOS_HEADER = "Download Videos"
SETUP_BLUETOOTH_HEADER = "Setup Bluetooth"
GENERATE_VIDEO_METADATA_OPTION = "Generate Video Metadata"
OPTIONS_ORDER = [WATCH_VIDEOS_HEADER,\
                 DOWNLOAD_VIDEOS_HEADER,\
                 SETUP_BLUETOOTH_HEADER,\
                 GENERATE_VIDEO_METADATA_OPTION]

GIANT_BOMB_INDIVIDUAL_EPISODES_HEADER = "GiantBomb (individual episodes)"

VIDEO_STOPPED_PREFIX = "Stopped at:"

def main():
    watchVideosOption = Option(browseVideos, None)
    downloadVideosOption = Option(downloadVideos, None)
    setupBluetoothOption = Option(setupBluetooth, None)
    generateVideoMetadataOption = Option(generateVideoMetadata, None)
    optionsDict =\
         {WATCH_VIDEOS_HEADER : watchVideosOption,\
          DOWNLOAD_VIDEOS_HEADER : downloadVideosOption,\
          SETUP_BLUETOOTH_HEADER : setupBluetoothOption,\
          GENERATE_VIDEO_METADATA_OPTION: generateVideoMetadataOption}
    menu = Menu(MAIN_HEADER, optionsDict, OPTIONS_ORDER)
    menu.start()
    
def browseVideos():
    browserMenu = FileBrowserMenu(WATCH_VIDEOS_HEADER, getRootDirectory(), playVideo, getVideoTitle, SUPPORTED_VIDEO_FORMATS)
    browserMenu.start()

def downloadVideos():
    optionsDict = {GIANT_BOMB_INDIVIDUAL_EPISODES_HEADER : Option(gbDownloadEps, None)}
    downloadVideosMenu = Menu(DOWNLOAD_VIDEOS_HEADER, optionsDict)
    downloadVideosMenu.start()

def gbDownloadEps():
    gbMenu = GiantBombMenu()
    gbMenu.start()

def generateVideoMetadata():
    generateVideoMetadataForDirectory(getRootDirectory())
    input("Press return to continue")

def generateVideoMetadataForDirectory(directory):
    for filePath in sorted(directory.files):
        generateVideoMetadataForFile(filePath)
    for subDir in sorted(directory.subDirectoriesDict.keys()):
        generateVideoMetadataForDirectory(directory.subDirectoriesDict[subDir])

def generateVideoMetadataForFile(filePath):
    if not isVideoFile(filePath):
        return
    if os.path.exists(getMetadataPath(filePath)):
        print(filePath)
        return
    try:
        videoDuration = int(float(FFProbe(filePath).streams[0].duration))
        metadataFile = open(getMetadataPath(filePath), 'w')
        metadataFile.write("00:00:00" + os.linesep)
        metadataFile.write(time.strftime("%H:%M:%S", time.gmtime(videoDuration)) + os.linesep)
        metadataFile.close()
        print(filePath)
    except:
        print(f"error reading info from [{filePath}]")

def isVideoFile(filePath):
    return os.path.splitext(filePath)[1] in SUPPORTED_VIDEO_FORMATS

def getMetadataPath(filePath):
    return f"{os.path.splitext(filePath)[0]}.{VIDEO_METADATA_FORMAT}"

def getRootDirectory():
    dirsDict = {}
    for root, dirs, files in os.walk(VIDEO_ROOT, topdown = False):
        filePaths = []
        for fileName in files:
            filePaths.append(os.path.join(root, fileName))
        directory = Directory(root, filePaths)
        dirsDict[root] = directory
        for dirName in dirs:
            directory.addSubDirectory(dirsDict[os.path.join(root, dirName)])
    return dirsDict[VIDEO_ROOT]

def setupBluetooth():
    os.system("pulseaudio -k")
    os.system("pulseaudio --start")
    os.system("bluetoothctl")

def playVideo(videoPath):
    metadata = getVideoMetadata(videoPath)
    cmdVideoPath = videoPath.replace(" ", "\\ ")
    cmdVideoPath = cmdVideoPath.replace("'", "\\'")
    cmdVideoPath = cmdVideoPath.replace("\"", "\\\"")
    if metadata and not getViewedRatio(metadata) >= 1.0:
        output = os.popen(RESUME_VIDEO_COMMAND_FORMAT.format(metadata[0], cmdVideoPath))
    else:
        output = os.popen(PLAY_VIDEO_COMMAND_FORMAT.format(cmdVideoPath))
    timeRegex = re.compile(r'\d{2}:\d{2}:\d{2}')
    stoppedTime = None
    while True:
        line = output.readline()
        if not line:
            break
        if VIDEO_STOPPED_PREFIX in line:
            stoppedTime = timeRegex.search(line).group()
    setVideoResumeTimeStamp(videoPath, stoppedTime)

def getVideoTitle(videoPath):
    metadata = getVideoMetadata(videoPath)
    if metadata:        
        return "{} - [{:.0%}]".format(os.path.basename(videoPath), getViewedRatio(metadata))
    else:
        return videoPath

def getVideoMetadata(videoPath):
    metadataPath = getMetadataPath(videoPath)
    if not os.path.exists(metadataPath):
        return None
    try:
        metadataFile = open(metadataPath, "r")
        resumeTime = metadataFile.readline().replace(os.linesep, '')
        duration = metadataFile.readline().replace(os.linesep, '')
        metadataFile.close()
        return (resumeTime, duration)
    except:
        return None

def getViewedRatio(metadata):
    return min(timestampToSec(metadata[0])/timestampToSec(metadata[1]), 1.0)

def setVideoResumeTimeStamp(videoPath, timestamp):
    metadata = getVideoMetadata(videoPath)
    if not metadata:
        return
    metadataFile = open(getMetadataPath(videoPath), "w")
    if timestamp:
        metadataFile.write(timestamp + os.linesep)
    else:
        # Assume that if the video was not stopped, it was finished
        metadataFile.write(metadata[1] + os.linesep)
    metadataFile.write(metadata[1] + os.linesep)
    metadataFile.close()

def timestampToSec(timestamp):
    h, m, s = timestamp.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

if __name__=="__main__":
    main()
