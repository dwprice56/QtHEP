#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (C) 2017 David Price
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, os.path, sys
# import time

sys.path.insert(0, '/home/dave/QtProjects/Helpers')
sys.path.insert(0, '/home/dave/QtProjects/DiscData')

# from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QTreeWidgetItem
# from PyQt5.QtCore import QProcess
from PyQt5.QtCore import QStandardPaths
from PyQt5.QtWidgets import (QApplication,
    QFileDialog,
    QMessageBox)

from  AppInit import __DEVELOPEMENT__

from MyMainWindow import MyMainWindow
from Disc import (Disc,
    DiscFilenameTemplatesSingleton,
    DiscPresetsSingleton)
from Preferences import Preferences
from SingletonLog import SingletonLog
from Titles import TitleVisibleSingleton

class MyApplication(QApplication):
    def __init__(self, arguments):
        super(MyApplication, self).__init__(arguments)

        self.mainWindow = None

        self.setApplicationName('QtHEP')
        QStandardPaths.setTestModeEnabled(__DEVELOPEMENT__)

        preferencesPath = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if (not os.path.exists(preferencesPath)):
            os.makedirs(preferencesPath)
        self.preferencesFilename = os.path.join(preferencesPath, 'QtHEP.preferences.xml')

        self.preferences = Preferences()
        if (os.path.exists(self.preferencesFilename)):
            self.preferences.FromXML(self.preferencesFilename)
        else:
            self.preferences.ToXML(self.preferencesFilename)
            # TODO log this action

        self.preferences.logging.InitLog()

        DiscFilenameTemplatesSingleton().Set(self.preferences.filenameTemplates)
        DiscPresetsSingleton().Set(self.preferences.presets.GetNames())

        self.disc = Disc(self)

        TitleVisibleSingleton().Set(self.preferences.autoTitle.minimumTitleSeconds,
            self.disc.hideShortTitles)

    @property
    def hashSessionFilename(self):
        """Return a session file name based on the disc hash value.

        This is built from the file hash value, an optional user entered prefix and the standard file extension."""

        return "{}.state.xml".format(self.disc.titles.GetHash())

    def SavePreferences(self):
        """Save the preferences to a file."""

        self.preferences.ToXML(self.preferencesFilename)
        self.mainWindow.statusBar.showMessage('Preferences saved to "{}".'.format(self.preferencesFilename), 15000)

def main():
    app = MyApplication(sys.argv)
    app.mainWindow = MyMainWindow()
    app.mainWindow.show()
    app.exec_()

if (__name__ == '__main__'):
    main()
