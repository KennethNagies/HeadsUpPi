#!/usr/bin/python3
import sys, termios, tty, os, time
import urllib.request
import json
sys.path.append('..')
from menu_util import Menu, Option

API_KEY="95d1f18da61b3ddc95a92b2cfba3cbf2da710964"
DOWNLOAD_DIRECTORY="/home/pi/Videos/Giant\\ Bomb"

MENU_HEADER = "Pick a GiantBomb Series"
FETCH_SHOWS_FORMAT = "https://www.giantbomb.com/api/video_shows/?api_key={}&format=json&field_list=id,title"
FETCH_EPISODES_FORMAT = "https://www.giantbomb.com/api/videos/?api_key={}&format=json&offset={}&filter=video_show:{}&field_list=name,low_url,image"
DOWNLOAD_EPISODE_FORMAT = "wget {}?api_key={} -O {}/{}/{}"
MAKE_SHOW_DIRECTORY_FORMAT = "mkdir {}/{}"

class Episode:

    def __init__(self, showName, episodeName, episodeUrl, iconUrl):
        self.showName = showName
        self.episodeName = episodeName
        self.episodeUrl = episodeUrl
        self.iconUrl = iconUrl

    def __str__(self):
        outStr = f"showName: [{self.showName}]{os.linesep}"
        outStr += f"episodeName: [{self.episodeName}]{os.linesep}"
        outStr += f"episodeUrl: [{self.episodeUrl}]{os.linesep}"
        outStr += f"iconUrl: [{self.iconUrl}]{os.linesep}"
        return outStr

class GiantBombMenu(Menu):

    def __init__(self):
        response = urllib.request.urlopen(FETCH_SHOWS_FORMAT.format(API_KEY))
        jsonString = response.read().decode("utf-8")
        jsonObject = json.loads(jsonString)
        shows = jsonObject["results"]
        self.showsDict = {}
        for show in shows:
            self.showsDict[show['title']] = show['id']
        optionsDict = {}
        for showName in self.showsDict.keys():
            option = Option(lambda x=showName: self.selectShow(x), None)
            optionsDict[showName] = option
        super().__init__(MENU_HEADER, optionsDict)

    def selectShow(self, showName):
        showId = self.showsDict[showName]
        episodes = []
        episodesFound = True
        offset = 0
        while episodesFound:
            response = urllib.request.urlopen(FETCH_EPISODES_FORMAT.format(API_KEY, offset, showId))
            jsonString = response.read().decode("utf-8")
            jsonObject = json.loads(jsonString)
            newEpisodes = jsonObject["results"]
            offset += len(newEpisodes)
            episodes.extend(newEpisodes)
            episodesFound = len(newEpisodes) > 0
        episodes.reverse()
        episodeCount = len(episodes)
        digits = 0
        while episodeCount % 10 > 0:
            episodeCount = int(episodeCount / 10)
            digits += 1
        episodesDict = {}
        episodeNum = 1
        for episode in episodes:
            episodeNumString = f"{str(episodeNum).zfill(digits)}"
            convertedEpisode = Episode(showName, f"{episodeNumString} - {episode['name']}", episode["low_url"], episode["image"]["icon_url"])
            episodesDict[convertedEpisode.episodeName] = Option(lambda x=convertedEpisode : downloadEpisode(x), None)
            episodeNum += 1
        showMenu = Menu(showName, episodesDict)
        showMenu.start()

def sanitizeForCommandLine(dirtyString):
    cleanString = dirtyString.replace(" ", "\\ ")
    cleanString = cleanString.replace("/", "\\/")
    cleanString = cleanString.replace(":", "\\:")
    cleanString = cleanString.replace("'", "\\'")
    cleanString = cleanString.replace('"', '\\"')
    cleanString = cleanString.replace("|", "\\|")
    cleanString = cleanString.replace("&", "\\&")
    return cleanString

def downloadEpisode(episode):
    cleanShowName = sanitizeForCommandLine(episode.showName)
    episodeExtension = episode.episodeUrl.split('.')[-1]
    cleanEpisodeFileName = f"{sanitizeForCommandLine(episode.episodeName)}.{episodeExtension}"
    iconExtension = episode.iconUrl.split('.')[-1]
    cleanIconFileName = f"{sanitizeForCommandLine(episode.episodeName)}.{iconExtension}"
    if not os.path.exists(f"{DOWNLOAD_DIRECTORY}/{cleanShowName}"):
        os.system(MAKE_SHOW_DIRECTORY_FORMAT.format(DOWNLOAD_DIRECTORY, cleanShowName))
    os.system(DOWNLOAD_EPISODE_FORMAT.format(episode.episodeUrl, API_KEY, DOWNLOAD_DIRECTORY, cleanShowName, cleanEpisodeFileName))
    os.system(DOWNLOAD_EPISODE_FORMAT.format(episode.iconUrl, API_KEY, DOWNLOAD_DIRECTORY, cleanShowName, cleanIconFileName))
    input("Press return to contine")


