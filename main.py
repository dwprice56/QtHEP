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

import argparse, os, os.path, sys
# import time

sys.path.insert(0, '/home/dave/QtProjects/Helpers')
sys.path.insert(0, '/home/dave/QtProjects/DiscData')

# from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QTreeWidgetItem
# from PyQt5.QtCore import QProcess
from PyQt5.QtCore import (
    QSettings,
    QStandardPaths
)
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox
)

from  AppInit import __DEVELOPEMENT__

from MyMainWindow import MyMainWindow
from Disc import (Disc,
    DiscFilenameTemplatesSingleton,
    DiscPresetsSingleton)
from Preferences import Preferences
from AudioTrackStates import DiscMixdownsSingleton
from Preferences import Preferences
from SingletonLog import SingletonLog
from Titles import TitleVisibleSingleton

class MyApplication(QApplication):
    def __init__(self, arguments):
        super().__init__(arguments)

        self.mainWindow = None

        self.setOrganizationName('QtHEP')
        self.setApplicationName('QtHEP')
        QStandardPaths.setTestModeEnabled(__DEVELOPEMENT__)

        preferencesPath = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if (not os.path.exists(preferencesPath)):
            os.makedirs(preferencesPath)
        self.preferencesFilename = os.path.join(preferencesPath, '{}.preferences.xml'.format(self.applicationName()))

        self.preferences = Preferences()
        if (os.path.exists(self.preferencesFilename)):
            self.preferences.fromXML(self.preferencesFilename)
            self.preferences.logging.initializeLog()
        else:
            self.preferences.toXML(self.preferencesFilename)

        DiscFilenameTemplatesSingleton().set(self.preferences.filenameTemplates)
        DiscMixdownsSingleton().set(self.preferences.mixdowns.getMixdowns())
        DiscPresetsSingleton().set(self.preferences.presets.getNames())

        self.disc = Disc(self)

        TitleVisibleSingleton().set(self.preferences.autoTitle.minimumTitleSeconds,
            self.disc.hideShortTitles)



        self.defaultSessionFilename = "{}.state.xml".format(self.applicationName())

        if __DEVELOPEMENT__:
        # 	self.settingsFilename = os.path.join(os.getcwd(), "{}.settings.xml".format(APP_NAME))
        # 	self.fullDefaultSessionFilename = os.path.join(os.getcwd(), self.defaultSessionFilename)
            s = os.path.join(os.getcwd(), 'TestFiles')
            self.temporarySessionFilename = os.path.join(s, "temp.{}".format(self.defaultSessionFilename))
        # 	self.logFilename = os.path.join(os.getcwd(), "{}.log".format(APP_NAME))
        else:
            if (os.path.exists(self.standardPaths.GetUserDataDir()) == False):
                os.makedirs(self.standardPaths.GetUserDataDir())
                SingletonLog().writeline('{} created'.format(self.standardPaths.GetUserDataDir()))

        # 	self.settingsFilename = os.path.join(self.standardPaths.GetUserDataDir(), "{}.settings.xml".format(APP_NAME))
        # 	self.fullDefaultSessionFilename = os.path.join(self.standardPaths.GetUserDataDir(), self.defaultSessionFilename)
            self.temporarySessionFilename = os.path.join(self.standardPaths.GetUserDataDir(), "temp.{}".format(self.defaultSessionFilename))
        # 	self.logFilename = os.path.join(self.standardPaths.GetDocumentsDir(), "{}.log".format(APP_NAME))

    def savePreferences(self):
        """ Save the preferences to a file.
        """
        self.preferences.toXML(self.preferencesFilename)
        self.mainWindow.statusBar.showMessage('Preferences saved to "{}".'.format(self.preferencesFilename), 15000)

def main(useDefaultGeometry, useDefaultWindowState):
    app = MyApplication(sys.argv)
    app.mainWindow = MyMainWindow()

    settings = QSettings()

    if (not useDefaultGeometry):
        geometry = settings.value('geometry')
        if (geometry):
            app.mainWindow.restoreGeometry(geometry)
    if (not useDefaultWindowState):
        windowState = settings.value('windowState')
        if (windowState):
            app.mainWindow.restoreState(windowState)

    app.mainWindow.show()
    app.exec_()

if (__name__ == '__main__'):
    parser = argparse.ArgumentParser()

    parser.add_argument('-dg', '--dg', action='store_true', help="Use the default geometry.")
    parser.add_argument('-ds', '--ds', action='store_true', help="Use the default window state.")

    args = parser.parse_args()

    main(args.dg, args.ds)
