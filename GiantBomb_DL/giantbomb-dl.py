#!/usr/bin/python3
import sys, termios, tty, os, time
import urllib.request
import json

API_KEY="95d1f18da61b3ddc95a92b2cfba3cbf2da710964"
DOWNLOAD_DIRECTORY="/home/pi/Videos/Giant Bomb"

class ShowsMenu:
    def clear():
        if os.name == "nt":
            _ = os.system("cls")
        else:
            _ = os.system("clear")

    def __init__(self, shows):
        self.shows = shows
        self.pageNum = 0
        self.maxPage = int(len(shows) / 10)
        if len(shows) % 10 == 0 and self.maxPage != 0:
            self.maxPage -= 1
        self.selectedShowId = shows[0]["id"]
        self.selectedShowTitle = shows[0]["title"]

    def display(self):
        ShowsMenu.clear()
        print("%d/%d: Shows" % (self.pageNum + 1, self.maxPage + 1))
        print("-----------------------------------------")
        for i in range(min(10, len(self.shows) - self.pageNum * 10)):
            print("%d: %s" % (i, self.shows[i + 10 * self.pageNum]["title"]))
        print("-----------------------------------------")
        print("(a <-) (d ->) (0-9 Select Show) (q Quit)")

    def nextPage(self):
        if self.pageNum < self.maxPage:
            self.pageNum += 1
        self.display()

    def prevPage(self):
        if self.pageNum > 0:
            self.pageNum -= 1
        self.display()

    def select(self, menuNum):
        if self.pageNum * 10 + menuNum >= len(self.shows):
            return
        else:
            self.selectedShowId = self.shows[10 * self.pageNum + menuNum]["id"]
            self.selectedShowTitle = self.shows[10 * self.pageNum + menuNum]["title"].replace("/", "")
            episodes = []
            episodesFound = True
            offset = 0
            while episodesFound:
                response = urllib.request.urlopen("https://www.giantbomb.com/api/videos/?api_key=%s&format=json&offset=%d&filter=video_show:%d&field_list=name,low_url,image" % (API_KEY, offset, self.selectedShowId))
                jsonString = response.read().decode("utf-8")
                jsonObject = json.loads(jsonString)
                newEpisodes = jsonObject["results"]
                offset += len(newEpisodes)
                episodes.extend(newEpisodes)
                episodesFound = len(newEpisodes) > 0
            episodes.reverse()
            ShowsMenu.clear()
            start = 0
            end = 0
            while True:
                entry = input("There are %d episodes. Enter the start and end of the range to download separated by a space: " % (len(episodes)))
                entry = entry.split(" ")
                if len(entry) != 2 or (not isInt(entry[0])) or (not isInt(entry[1])):
                    ShowsMenu.clear()
                    print("Invalid entry.")
                    continue
                start = int(entry[0])
                end = int(entry[1])
                break
            if not os.path.exists("%s/%s" % (DOWNLOAD_DIRECTORY, self.selectedShowTitle)):
                os.system("mkdir '%s/%s'" % (DOWNLOAD_DIRECTORY, self.selectedShowTitle))
            for i in range(start - 1, end):
                fileType = episodes[i]["low_url"].split(".")[-1]
                command = "wget %s?api_key=%s -O '%s/%s/%s'" % (episodes[i]["low_url"], API_KEY, DOWNLOAD_DIRECTORY, self.selectedShowTitle, episodes[i]["name"].replace("/", "-").replace(":", "") + "." + fileType)
                os.system(command)
                fileType = episodes[i]["image"]["icon_url"].split(".")[-1]
                command = "wget --header='User-Agent: Kenneth-DLNA-App' %s?api_key=%s -O '%s/%s/%s'" % (episodes[i]["image"]["icon_url"], API_KEY, DOWNLOAD_DIRECTORY, self.selectedShowTitle, episodes[i]["name"].replace("/", "-").replace(":", "") + "." + fileType)
                os.system(command)
            print("--------------------------------------------------")
            print("Download Complete.")

def isInt(s):
    try:
        int(s)
        return True
    except:
        return False

def getChar():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

BUTTON_DELAY = 0.1

def main():
    response = urllib.request.urlopen("https://www.giantbomb.com/api/video_shows/?api_key=%s&format=json&field_list=id,title" % (API_KEY))
    jsonString = response.read().decode("utf-8")
    jsonObject = json.loads(jsonString)
    shows = jsonObject["results"]
    shows.sort(key=lambda obj: obj["title"])
    showsMenu = ShowsMenu(shows)
    showsMenu.display()
    while True:
        char = getChar()
        if char == "a":
            showsMenu.prevPage()
        if char == "d":
            showsMenu.nextPage()
        elif char >= "0" and char <= "9":
            showsMenu.select(int(char))
            break
        elif char == "q":
            break


if __name__=="__main__":
    main()
