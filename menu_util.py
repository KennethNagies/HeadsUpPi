#!/usr/bin/python3
import os, sys, termios, tty

BARRIER = "-----------------------------------------------------"
HEADER_FORMAT = "{}/{}: {}"
SELECTION_FORMAT = "{}: {}"
FOOTER = "(a <-) (d ->) (0-9 Select) (q Quit)"

class Option:
    def __init__(self, selectFunc, titleFunc):
        self.selectFunc = selectFunc
        self.titleFunc = titleFunc

class Menu:

    # This sets up the menu based on the provided options
    # If no sortedOptions are provided for the options, the options will be presented in alphabetical order
    def __init__(self, header, optionsDict, sortedOptions):
        self.header = header
        self.optionsDict = optionsDict
        self.sortedOptions = self.getSortedOptions(sortedOptions)
        self.currentPage = 0
        self.maxPage = int(len(optionsDict) / 10)
        if len(optionsDict) % 10 == 0 and self.maxPage != 0:
            self.maxPage -= 1
        self.quit = False
        self.navUp = False

    def start(self):
        self.display()
        while True:
            if self.quit:
                break
            char = Menu.getChar()
            if char == "a":
                self.prevPage()
            elif char == "d":
                self.nextPage()
            elif char >= "0" and char <= "9":
                self.select(int(char))
                if self.navUp:
                    break
            elif char == "q":
                self.quit = True
                break
        clear()

    def display(self):
        clear()
        self.printHeader()
        rangeStart = self.currentPage * 10
        rangeEnd = min(rangeStart + 10, len(self.optionsDict))
        for i in range(rangeStart, rangeEnd):
            option = self.optionsDict[self.sortedOptions[i]]
            if option.titleFunc:
                print(SELECTION_FORMAT.format(i % 10, option.titleFunc()))
            else:
                print(SELECTION_FORMAT.format(i % 10, self.sortedOptions[i]))
        self.printFooter()

    def getSortedOptions(self, sortedOptions):
        if sortedOptions is None or len(sortedOptions) == 0:
            return sorted(self.optionsDict.keys())
        elif len(sortedOptions) != len(self.optionsDict):
            raise ValueError("Length of sorted options does not match length of options dict")
        else:
            for key in sortedOptions:
                if not key in self.optionsDict:
                    raise ValueError(f'key: \"{key}\" not found in optionsDict')
            return sortedOptions

    def printHeader(self):
        print(HEADER_FORMAT.format(self.currentPage + 1, self.maxPage + 1, self.header))
        print(BARRIER)

    def printFooter(self):
        print(BARRIER)
        print(FOOTER)

    def nextPage(self):
        if self.currentPage < self.maxPage:
            self.currentPage += 1
        self.display()

    def prevPage(self):
        if (self.currentPage > 0):
            self.currentPage -= 1
        self.display()

    def select(self, index):
        optionIndex = self.currentPage * 10 + index
        if optionIndex >= len(self.optionsDict):
            self.display()
            return
        option = self.sortedOptions[optionIndex]
        self.optionsDict[option].selectFunc()
        self.display()

    def getChar():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class Directory:
    def __init__(self, path, files):
        self.path = path
        self.subDirectoriesDict = {}
        self.files = files

    def addSubDirectory(self, subDirectory):
        self.subDirectoriesDict[subDirectory.path] = subDirectory

    def __str__(self):
        outStr = f"{self.path}\n"
        for file in sorted(self.files):
            outStr += f"{file}\n"
        for subDir in sorted(self.subDirectoriesDict.keys()):
            outStr += self.subDirectoriesDict[subDir].__str__()
        return outStr

class FileBrowserMenu(Menu):
    UP_DIRECTORY = Directory("../", [])

    def __init__(self, header, baseDirectory, fileSelectFunc, fileTitleFunc, supportedFormats, isBase = True):
        self.baseDirectory = baseDirectory
        self.fileSelectFunc = fileSelectFunc
        self.fileTitleFunc = fileTitleFunc
        self.isBase = isBase
        self.supportedFormats = supportedFormats
        super().__init__(header, self.getOptionsDict(), self.getFileBrowserSortedOptions())

    def getOptionsDict(self):
        optionsDict = {}
        if not self.isBase:
            upOption = Option(lambda x=self.UP_DIRECTORY : self.openDirectory(x), None)
            optionsDict[self.UP_DIRECTORY.path] = upOption
        for subDirectory in self.baseDirectory.subDirectoriesDict.values():
            dirName = subDirectory.path.replace(self.baseDirectory.path + '/', '')
            dirOption = Option(lambda x=subDirectory : self.openDirectory(x), None)
            optionsDict[dirName] = dirOption
        for fileName in self.baseDirectory.files:
            shortFileName = fileName.replace(self.baseDirectory.path + '/', '')
            if self.isValidFile(shortFileName):
                fileOption = Option(lambda x=fileName : self.fileSelectFunc(x), lambda y=fileName : self.fileTitleFunc(y))
                optionsDict[shortFileName] = fileOption
        return optionsDict

    def getFileBrowserSortedOptions(self):
        sortedOptions = []
        if not self.isBase:
            sortedOptions.append(self.UP_DIRECTORY.path)
        for dirName in sorted(self.baseDirectory.subDirectoriesDict.keys()):
            sortedOptions.append(dirName.replace(self.baseDirectory.path + '/', ''))
        for fileName in sorted(self.baseDirectory.files):
            if (self.isValidFile(fileName)):
                sortedOptions.append(fileName.replace(self.baseDirectory.path + '/', ''))
        return sortedOptions

    def isValidFile(self, fileName):
        for supportedFormat in self.supportedFormats:
            if fileName.endswith(supportedFormat):
                return True
        return False

    def openDirectory(self, directory):
        if (directory == self.UP_DIRECTORY):
            self.navUp = True
            return
        folderMenu = FileBrowserMenu(self.header, directory, self.fileSelectFunc, self.fileTitleFunc, self.supportedFormats, False)
        folderMenu.start()
        self.quit = folderMenu.quit


def clear():
    if os.name == "nt":
        _ = os.system("cls")
    else:
        _ = os.system("clear")

