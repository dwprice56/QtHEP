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

import copy, os.path, pathlib, sys

sys.path.insert(0, '/home/dave/QtProjects/Helpers')

from SingletonLog import SingletonLog

from PyQt5Helpers import UpdateComboBox
from PyQt5WidgetDataConnectors import (WidgetDataConnectors,
    QCheckBoxDataConnector,
    QComboBoxDataConnector,
    QLineEditDataConnector,
    QSpinBoxDataConnector)

from PyQt5OrderedEditableList import QOrderedEditableList
from PyQt5Validators import (_DEFAULT_TITLE as VALIDATORS_DEFAULT_TITLE,
    QLineEditor_Abstract_Validator,
    QLineEdit_FileExists_Validator,
    QLineEdit_FolderExists_Validator,
    QLineEdit_ExecutableExists_Validator,
    QLineEdit_NotBlank_Validator,
    QListWidget_NotEmpty_Validator)

from Preferences import FilenameTemplates, Mixdown

# from PyQt5 import uic
from PyQt5.QtCore import Qt, QDir, QStandardPaths
from PyQt5.QtWidgets import (QApplication,
    QDialog,
    QFileDialog,
    QListWidgetItem,
    QMessageBox)

from preferencesui import Ui_DialogPreferences

# TODO add set defaults button
# TODO update combo boxes when mixdowns change
# TODO update parent combo boxes when dialog closes

class LogFile_Validator(QLineEditor_Abstract_Validator):
    """ A validator for a QLineEdit field that contains a file.

        The file must exist.
    """

    __DEFAULT_MESSAGE = 'The Log File field is either blank or does not point to a valid file.'

    def __init__(self, widget, title=VALIDATORS_DEFAULT_TITLE, message=__DEFAULT_MESSAGE):
        super(LogFile_Validator, self).__init__(widget, title, message)

    def isValid(self):
        """ Validate the name of the log file.

            The log filename is valid if:
                1) The file exists.
                2) The file can be created.

            Try to create the log file if it does not exist.
        """

        if (self._flags & self.FLAG_CLEAR_HIGHLIGHT_BEFORE_VALIDATING):
            self.clearHighlight()

        if ((self._flags & self.FLAG_DISABLED_WIDGET_ALWAYS_VALID)
            and (not self._widget.isEnabled())):
            return True

        log = SingletonLog()

        path = pathlib.Path(self._widget.text())
        if (path.is_file()):
            return True

        result = QMessageBox.question(QApplication.instance().mainWindow, 'Create Log File?',
            'Log file {} does not exist.  Do you want to create it?'.format(path.name))
        if (result == QMessageBox.Yes):
            try:
                path.touch(exist_ok=False)
                QMessageBox.information(QApplication.instance().mainWindow, 'Create Log File',
                    'Log file {} was created.'.format(path.name))

                return True

            except (FileExistsError, Exception) as err:
                QMessageBox.critical(QApplication.instance().mainWindow, 'Create Log File Error',
                    'Unable to create log file "{}".\n{}'.format(path.name, err))

        if (self._flags & self.FLAG_HIGHLIGHT_WIDGETS_WITH_ERRORS):
            self.setHighlight()

        if (self._flags & self.FLAG_SHOW_ERROR_MESSAGE):
            QMessageBox.critical(QApplication.instance().mainWindow, self._errorTitle, self._errorMessage)

        return False

class PreferencesDialog(QDialog, Ui_DialogPreferences):
    """ The dialog used to edit the application preferences."""

    # PROBLEM_BACKGROUND_STYLE = 'background-color: rgb(252, 175, 62);'

    def __init__(self, preferences, parent=None):
        super(PreferencesDialog, self).__init__(parent)
        self.setupUi(self)

        self.__preferences = preferences
        self.__widgetDataConnectors = WidgetDataConnectors()

        # Some widgets are initialized in separate method to simplify this method.
        self.__initGeneralTab()
        self.__initFileNameTab()
        self.__initPresetsTab()
        self.__initMixdownTab()
        self.__initDiscSessionTab()
        self.__initAuto1Tab()
        self.__initAuto2Tab()

    def __initAuto1Tab(self):
        """ Initialize the widgets on the Auto1 tab.

            These widgets are only initialized in a separate method to simplify
            the __init__() method.
        """

        # Connect the widgets to the data items.
        # ======================================================================

        # Auto Titles
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoSelectLongestTitle, self.__preferences.autoTitle, 'autoSelectLongestTitle'))
        self.__widgetDataConnectors.append(QSpinBoxDataConnector(
            self.spinBox_AutoShortTitleSeconds, self.__preferences.autoTitle, 'minimumTitleSeconds'))

        # Auto Audio Track(s)
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoAudioPreferredLanguage, self.__preferences.autoAudioTracks, 'autoSelectPreferredLanguage'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_AutoAudioPreferredLanguage, self.__preferences.autoAudioTracks, 'preferredLanguage'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoAudioSelect51, self.__preferences.autoAudioTracks, 'autoSelect51'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoAudioSelectDTS, self.__preferences.autoAudioTracks, 'autoSelectDTS'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoAudioFallback, self.__preferences.autoAudioTracks, 'autoSelectFallback'))

        # Auto Subtitle Track(s)
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoSubtitlePreferredLanguage, self.__preferences.autoSubtitle, 'autoSelectPreferredLanguage'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_AutoSubtitlePreferredLanguage, self.__preferences.autoSubtitle, 'preferredLanguage'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoSubtitleFirstTrack, self.__preferences.autoSubtitle, 'autoSelectSubtitle'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoSubtitleBurnIn, self.__preferences.autoSubtitle, 'subtitleBurn'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoSubtitleDefault, self.__preferences.autoSubtitle, 'subtitleDefault'))

        # Create the validators.
        # ======================================================================

        # Auto Audio Track(s)
        self.Validator_AutoAudioPreferredLanguage = QLineEdit_NotBlank_Validator(self.lineEdit_AutoAudioPreferredLanguage,
            message = 'The Audio Track Preffered Language field may not be blank.')

        # Auto Subtitle Track(s)
        self.Validator_AutoSubtitlePreferredLanguage = QLineEdit_NotBlank_Validator(self.lineEdit_AutoSubtitlePreferredLanguage,
            message = 'The Subtitle Track Preferred Language field may not be blank.')

    def __initAuto2Tab(self):
        """ Initialize the widgets on the Auto2 tab.

            These widgets are only initialized in a separate method to simplify
            the __init__() method.
        """

        # Connect the widgets to the data items.
        # ======================================================================

        # Auto Audio Mixdowns
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownAC3_51_Primary, self.__preferences.autoMixdown, 'ac351Primary'))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownAC3_51_Secondary, self.__preferences.autoMixdown, 'ac351Secondary'))

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownDTS_Primary, self.__preferences.autoMixdown, 'dtsPrimary'))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownDTS_Secondary, self.__preferences.autoMixdown, 'dtsSecondary'))

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownDTSHD_Primary, self.__preferences.autoMixdown, 'dtshdPrimary'))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownDTSHD_Secondary, self.__preferences.autoMixdown, 'dtshdSecondary'))

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownAC3_Primary, self.__preferences.autoMixdown, 'ac3Primary'))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownAC3_Secondary, self.__preferences.autoMixdown, 'ac3Secondary'))

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownDefault_Primary, self.__preferences.autoMixdown, 'otherPrimary'))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_AutoAudioMixdownDefault_Secondary, self.__preferences.autoMixdown, 'otherSecondary'))

        # Auto Crop
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoCropReset, self.__preferences.autoCrop, 'autoResetCrop'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_AutoCropCopyLongestTitle, self.__preferences.autoCrop, 'autoCopyCrop'))

    def __initDiscSessionTab(self):
        """ Initialize the widgets on the Disc Session tab.

            These widgets are only initialized in a separate method to simplify
            the __init__() method.
        """

        self.pushButton_BrowseAutomaticSessionFolder.clicked.connect(self.onBrowseAutomaticSessionFolder)

        # Connect the widgets to the data items.
        # ======================================================================

        # Automaic Disc Sessions
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_DiscSessionsAutoDiscSessions, self.__preferences.discSession, 'autoDiscSessions'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_DiscSessionAutomaticSessionsFolder, self.__preferences.discSession, 'autoDiscSessionsFolder'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_DiscSessionAutomaticFilenamePrefix, self.__preferences.discSession, 'autoDiscSessionsPrefix'))

        # Load Session
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_LoadSessionKeepPosition, self.__preferences.discSession, 'keepPosition'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBoxLoadSessionKeepSize, self.__preferences.discSession, 'keepSize'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBoxLoadSessionKeepDestination, self.__preferences.discSession, 'keepDestination'))

        # New Source
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_SelectFirstMask, self.__preferences.newSource, 'firstMask'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_SelectFirstPreset, self.__preferences.newSource, 'firstPreset'))

        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_DefaultDestination, self.__preferences.newSource, 'useDefaultDestination'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_DefaultDestination, self.__preferences.newSource, 'defaultDestination'))

        # Create the validators.
        # ======================================================================

        # Automaic Disc Sessions
        self.Validator_DiscSessionAutomaticSessionsFolder = QLineEdit_FolderExists_Validator(self.lineEdit_DiscSessionAutomaticSessionsFolder,
            message = 'The Automatic Sessions Folder field is either blank or does not point to a valid folder.')

        # New Source
        self.Validator_DefaultDestination = QLineEdit_FolderExists_Validator(self.lineEdit_DefaultDestination,
            message = 'The Default Destination Folder field is either blank or does not point to a valid folder.')

    def __initFileNameTab(self):
        """ Initialize the widgets on the File Name tab.

            These widgets are only initialized in a separate method to simplify
            the __init__() method.
        """

        self.filenameTemplatesOrderedEditableList = QOrderedEditableList(self,
            self.listWidget_FilenameTemplates,
            self.toolButton_FilenameTemplateAdd,
            self.toolButton_FilenameTemplateCopy,
            self.toolButton_FilenameTemplateDelete,
            self.toolButton_FilenameTemplateMoveTop,
            self.toolButton_FilenameTemplateUp,
            self.toolButton_FilenameTemplateMoveDown,
            self.toolButton_FilenameTemplateMoveBottom,
            self.__preferences.filenameTemplates.DEFAULT_FILENAME_TEMPLATES[0]
        )

        # Connect the widgets to the data items.
        # ======================================================================

        # File Name Replacement
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_FilenameCharacterReplace, self.__preferences.filenameReplacement, 'replaceFilenameCharacters'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_FilenameCharacterReplaceWith, self.__preferences.filenameReplacement, 'replacementFilenameCharacter'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_FilenameCharactersToReplace, self.__preferences.filenameReplacement, 'filenameCharactersToReplace'))

        # Create the validators.
        # ======================================================================
        self.Validator_FilenameTemplates = QListWidget_NotEmpty_Validator(self.listWidget_FilenameTemplates,
            message = 'The File Name Templates list may not be blank.')

        # File Name Replacement
        self.Validator_FilenameCharacterReplaceWith = QLineEdit_NotBlank_Validator(self.lineEdit_FilenameCharacterReplaceWith,
            message = 'The Filename Character Replace With field may not be blank.')
        self.Validator_FilenameCharactersToReplace = QLineEdit_NotBlank_Validator(self.lineEdit_FilenameCharactersToReplace,
            message = 'The Filename Characters To Replace field may not be blank.')

    def __initGeneralTab(self):
        """ Initialize the widgets on the General tab.

            These widgets are only initialized in a separate method to simplify
            the __init__() method.
        """

        self.pushButton_BrowseHandBrakeCLI.clicked.connect(self.onBrowseHandBrakeCLI)
        self.pushButton_BrowseVLC.clicked.connect(self.onBrowseVLC)

        self.pushButton_BrowseLogFile.clicked.connect(self.onBrowseLogFile)
        self.pushButton_ClearLogFile.clicked.connect(self.onClearLogFile)

        # self.checkBox_LogHandBrakeAnalysis.toggled.connect(self.SetEnabledLogFilename)
        # self.checkBox_LogHandBrakeTranscoding.toggled.connect(self.SetEnabledLogFilename)
        self.lineEdit_LogFilename.textChanged.connect(self.SetEnabledClearLog)

        self.pushButton_BrowseDefaultDestination.clicked.connect(self.onBrowseDefaultDestinationFolder)

        # Connect the widgets to the data items.
        # ======================================================================

        # Executables
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_HandBrakeCLI, self.__preferences.executables, 'handBrakeCLI'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_VLC, self.__preferences.executables, 'VLC'))

        # Logging
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_LogHandBrakeAnalysis, self.__preferences.logging, 'analysis'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_LogHandBrakeTranscoding, self.__preferences.logging, 'commandsAndTimestamps'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_LogFilename, self.__preferences.logging, 'filename'))

        # Options
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_ChapterNameNumbers, self.__preferences.options, 'numberChapterNames'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_MP4StreamWarning, self.__preferences.options, 'checkMp4Audio'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_SetShortLastChapter, self.__preferences.options, 'checkImportShortChapter'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_ShortLastChapter, self.__preferences.options, 'textImportShortChapter'))

        # Create the validators.
        # ======================================================================

        # Executables
        self.Validator_HandBrakeCLI = QLineEdit_ExecutableExists_Validator(self.lineEdit_HandBrakeCLI,
            message = 'The HandBrakeCLI field is either blank or does not point to a valid executable.')
        self.Validator_VLC = QLineEdit_ExecutableExists_Validator(self.lineEdit_VLC,
            message = 'The VLC field is either blank or does not point to a valid executable.')

        # Logging
        self.Validator_LogFilename = LogFile_Validator(self.lineEdit_LogFilename)

        # Options
        self.Validator_ShortLastChapter = QLineEdit_NotBlank_Validator(self.lineEdit_ShortLastChapter,
            message = 'The Short Last Chapter field may not be blank.')

    def __initMixdownTab(self):
        """ Initialize the widgets on the Mixdown tab.

            These widgets are only initialized in a separate method to simplify
            the __init__() method.
        """

        self.mixdownsOrderedEditableList = QOrderedEditableList(self,
            self.listWidget_Mixdowns,
            self.toolButton_MixdownAdd,
            self.toolButton_MixdownCopy,
            self.toolButton_MixdownDelete,
            self.toolButton_MixdownMoveTop,
            self.toolButton_MixdownUp,
            self.toolButton_MixdownMoveDown,
            self.toolButton_MixdownMoveBottom,
            'New Mixdown',
            self.onNewMixdownListItem
        )

        # Connect the widgets to the data items.
        # ======================================================================
        self.listWidget_Mixdowns.currentItemChanged.connect(self.onMixdownListWidgetCurrentItemChanged)

        # Create the validators.
        # ======================================================================
        self.Validator_Mixdowns = QListWidget_NotEmpty_Validator(self.listWidget_Mixdowns,
            message = 'The Mixdowns list may not be blank.')

    def __initPresetsTab(self):
        """ Initialize the widgets on the Presets tab.

            These widgets are only initialized in a separate method to simplify
            the __init__() method.
        """

        self.presetsOrderedEditableList = QOrderedEditableList(self,
            self.listWidget_Presets,
            self.toolButton_PresetAdd,
            self.toolButton_PresetCopy,
            self.toolButton_PresetDelete,
            self.toolButton_PresetMoveTop,
            self.toolButton_PresetUp,
            self.toolButton_PresetMoveDown,
            self.toolButton_PresetMoveBottom,
            'New Preset',
            self.onNewPresetListItem
        )

        # Connect the widgets to the data items.
        # ======================================================================
        self.listWidget_Presets.currentItemChanged.connect(self.onPresetListWidgetCurrentItemChanged)

        # Create the validators.
        # ======================================================================
        self.Validator_Presets = QListWidget_NotEmpty_Validator(self.listWidget_Presets,
            message = 'The Presets list may not be blank.')

    def accept(self):
        if (self.Validate()):
            super(PreferencesDialog, self).accept()

    def LoadAutoMixdownComboBoxes(self):
        """ The Auto Mixdown combo boxes must be loaded from the mixdown list
            box to pick up any changes to the mixdown list before the preferences
            dialog is closed.  That means the mixdown list box must be loaded
            before the combo boxes can be loaded.
        """

        names = ['']

        for i in range(self.listWidget_Mixdowns.count()):
            names.append(self.listWidget_Mixdowns.item(i).text())

        UpdateComboBox(self.comboBox_AutoAudioMixdownAC3_51_Primary, names)
        UpdateComboBox(self.comboBox_AutoAudioMixdownAC3_51_Secondary, names)

        UpdateComboBox(self.comboBox_AutoAudioMixdownDTS_Primary, names)
        UpdateComboBox(self.comboBox_AutoAudioMixdownDTS_Secondary, names)

        UpdateComboBox(self.comboBox_AutoAudioMixdownDTSHD_Primary, names)
        UpdateComboBox(self.comboBox_AutoAudioMixdownDTSHD_Secondary, names)

        UpdateComboBox(self.comboBox_AutoAudioMixdownAC3_Primary, names)
        UpdateComboBox(self.comboBox_AutoAudioMixdownAC3_Secondary, names)

        UpdateComboBox(self.comboBox_AutoAudioMixdownDefault_Primary, names)
        UpdateComboBox(self.comboBox_AutoAudioMixdownDefault_Secondary, names)

    def onBrowseAutomaticSessionFolder(self):
        """ Browse for the location of the automatic session.
        """

        sessionsFolder = QFileDialog.getExistingDirectory(QApplication.instance().mainWindow,
            'Select Automatic Sessions Folder', self.lineEdit_DiscSessionAutomaticSessionsFolder.text())
        if (not sessionsFolder):
            return

        self.lineEdit_DiscSessionAutomaticSessionsFolder.setText(sessionsFolder)

    def onBrowseDefaultDestinationFolder(self):
        """ Browse for the location of the default destination folder.
        """

        destinationFolder = QFileDialog.getExistingDirectory(QApplication.instance().mainWindow,
            'Select Default Destination Folder', self.lineEdit_DefaultDestination.text())
        if (not destinationFolder):
            return

        self.lineEdit_DefaultDestination.setText(destinationFolder)

    def onBrowseHandBrakeCLI(self):
        """ Browse for the location of the HandBrakeCLI.
        """

        dlg = QFileDialog(QApplication.instance().mainWindow, 'Select HandBrakeCLI',
            self.lineEdit_HandBrakeCLI.text())
        dlg.setNameFilters(['HandbrakeCLI (H*, H*.exe)', 'All files (*, *.*)'])
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setFilter(QDir.Files | QDir.Executable)

        result = dlg.exec_()
        if (result):
            self.lineEdit_HandBrakeCLI.setText(dlg.selectedFiles()[0])

        del dlg

    def onBrowseLogFile(self):
        """ Browse for the location of the log file.
        """

        dlg = QFileDialog(QApplication.instance().mainWindow, 'Select Log File',
            self.lineEdit_LogFilename.text())
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setDefaultSuffix('txt')
        dlg.setFilter(QDir.Files | QDir.Writable)
        dlg.setNameFilters(['Text files (*.txt)', 'All files (*, *.*)'])

        result = dlg.exec_()
        if (result):
            self.lineEdit_LogFilename.setText(dlg.selectedFiles()[0])

        del dlg

    def onBrowseVLC(self):
        """ Browse for the location of the VLC executable.
        """
        dlg = QFileDialog(QApplication.instance().mainWindow, 'Find VLC',
            self.lineEdit_VLC.text())
        dlg.setNameFilters(['VLC files (V*, V*.exe)', 'All files (*, *.*)'])
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setFilter(QDir.Files | QDir.Executable)

        result = dlg.exec_()
        if (result):
            self.lineEdit_VLC.setText(dlg.selectedFiles()[0])

        del dlg

    def onClearLogFile(self):
        """ Clear the log file.
        """

        log = SingletonLog()
        log.clear()

        QApplication.instance().mainWindow.statusBar.showMessage('Log file cleared.', 15000)

    def onMixdownListWidgetCurrentItemChanged(self, current, previous):
        """ The detail fields for a mixdown list item must be updated whenever
            the item selection changes.
        """

        if (previous is not None):
            mixdown = previous.data(Qt.UserRole)
            mixdown.tag = self.lineEdit_MixdownTag.text()
            mixdown.encoder = self.lineEdit_MixdownEncoder.text()
            mixdown.mixdown = self.lineEdit_MixdownMixdown.text()
            mixdown.sampleRate = self.lineEdit_MixdownSampleRate.text()
            mixdown.bitrate = self.lineEdit_MixdownBitrate.text()
            mixdown.dynamicRangeCompression = self.lineEdit_MixdownDynamicRangeCompression.text()
            mixdown.gain = self.lineEdit_MixdownGain.text()

        if (current is not None):
            mixdown = current.data(Qt.UserRole)
            self.lineEdit_MixdownTag.setText(mixdown.tag)
            self.lineEdit_MixdownEncoder.setText(mixdown.encoder)
            self.lineEdit_MixdownMixdown.setText(mixdown.mixdown)
            self.lineEdit_MixdownSampleRate.setText(mixdown.sampleRate)
            self.lineEdit_MixdownBitrate.setText(mixdown.bitrate)
            self.lineEdit_MixdownDynamicRangeCompression.setText(mixdown.dynamicRangeCompression)
            self.lineEdit_MixdownGain.setText(mixdown.gain)

    def onNewMixdownListItem(self, item, name):
        """ Add a new Mixdown() object to item.data() to complete the item
            initialization.
        """

        mixdown = self.__preferences.mixdowns.NewMixdown()
        mixdown.name = name
        item.setData(Qt.UserRole, mixdown)

    def onNewPresetListItem(self, item, name):
        """ Add a new Preset() object to item.data() to complete the item
            initialization.
        """

        preset = self.__preferences.presets.NewPreset()
        preset.name = name
        item.setData(Qt.UserRole, preset)

    def onPresetListWidgetCurrentItemChanged(self, current, previous):
        """ The detail fields for a mixdown list item must be updated whenever
            the item selection changes.
        """

        if (previous is not None):
            preset = previous.data(Qt.UserRole)
            preset.tag = self.lineEdit_PresetTag.text()
            preset.settings = self.plainTextEdit_PresetSettings.toPlainText()

        if (current is not None):
            preset = current.data(Qt.UserRole)
            self.lineEdit_PresetTag.setText(preset.tag)
            self.plainTextEdit_PresetSettings.setPlainText(preset.settings)

    def SetEnabledClearLog(self):
        """ Enable pushButton_ClearLogFile if the log file exists, otherwise
            disable it.
        """

        enabled = (os.path.exists(self.lineEdit_LogFilename.text())
            and os.path.isfile(self.lineEdit_LogFilename.text()))
        self.pushButton_ClearLogFile.setEnabled(enabled)

    # def SetEnabledLogFilename(self, checked):
    #     """ Enables lineEdit_LogFilename if either checkBox_LogHandBrakeAnalysis
    #         or checkBox_LogHandBrakeTranscoding is checked.  Otherwise, it
    #         disables it.
    #     """
    #
    #     enabled = (self.checkBox_LogHandBrakeAnalysis.isChecked()
    #         or self.checkBox_LogHandBrakeTranscoding.isChecked())
    #
    #     self.lineEdit_LogFilename.setEnabled(enabled)
    #     self.pushButton_BrowseLogFile.setEnabled(enabled)

    def TransferFromWindow(self):
        """ Copy the data from the preferences object to the dialog widgets.
        """

        self.__widgetDataConnectors.transferFromWidgets()

        # File Name templates
        self.__preferences.filenameTemplates.clear()
        for i in range(self.listWidget_FilenameTemplates.count()):
            item = self.listWidget_FilenameTemplates.item(i)
            self.__preferences.filenameTemplates.append(item.text())

        # Mixdowns
        self.onMixdownListWidgetCurrentItemChanged(None, self.listWidget_Mixdowns.currentItem())
        self.__preferences.mixdowns.clear()
        for i in range(self.listWidget_Mixdowns.count()):
            item = self.listWidget_Mixdowns.item(i)
            mixdown = item.data(Qt.UserRole)

            # Ideally, the name in the mixdown object would be updated when the
            # item text is changed.  Sadly, Qt5 does not do any of the following:
            #
            #   1) Emit a signal from a QListWidget or a QListWidgetItem when
            #      when the list item text is edited/changed.
            #   2) Emit a signal when a persistent editor is closed.
            #
            # Annoyingly, Qt5 also does not seem to provide a way to:
            #
            #   1) Get the persistent editor for a QListWidget or a QListWidgetItem.
            #   2) Determine if a persistent editor is open.
            #
            # So, mixdown.name must be updated before the mixdown object is
            # added to the mixdowns list.
            mixdown.name = item.text()

            self.__preferences.mixdowns.append(mixdown)

        # Presets
        self.onPresetListWidgetCurrentItemChanged(None, self.listWidget_Presets.currentItem())
        self.__preferences.presets.clear()
        for i in range(self.listWidget_Presets.count()):
            item = self.listWidget_Presets.item(i)
            preset = item.data(Qt.UserRole)

            # See the above mixdown comments.
            preset.name = item.text()
            self.__preferences.presets.append(preset)

    def TransferToWindow(self):
        """ Copy the data from the preferences object to the dialog widgets.
        """

        # File Name Templates
        for filenameTemplate in self.__preferences.filenameTemplates:
            item = QListWidgetItem(filenameTemplate, self.listWidget_FilenameTemplates)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.filenameTemplatesOrderedEditableList.EnableButtons()

        # Mixdowns
        for mixdown in self.__preferences.mixdowns:
            item = QListWidgetItem(mixdown.name, self.listWidget_Mixdowns)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            item.setData(Qt.UserRole, copy.deepcopy(mixdown))
        self.mixdownsOrderedEditableList.EnableButtons()

        # Presets
        for preset in self.__preferences.presets:
            item = QListWidgetItem(preset.name, self.listWidget_Presets)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            item.setData(Qt.UserRole, copy.deepcopy(preset))
        self.presetsOrderedEditableList.EnableButtons()

        # Auto Audio Mixdowns
        self.LoadAutoMixdownComboBoxes()

        self.__widgetDataConnectors.transferToWidgets()

        # New Source
        self.lineEdit_DefaultDestination.setEnabled(self.__preferences.newSource.useDefaultDestination)
        self.pushButton_BrowseDefaultDestination.setEnabled(self.__preferences.newSource.useDefaultDestination)

        # Logging
        self.SetEnabledClearLog()
        # self.SetEnabledLogFilename(True)

        # Options
        self.lineEdit_ShortLastChapter.setEnabled(self.__preferences.options.checkImportShortChapter)

        # File Name Replacement
        self.lineEdit_FilenameCharacterReplaceWith.setEnabled(self.__preferences.filenameReplacement.replaceFilenameCharacters)
        self.lineEdit_FilenameCharactersToReplace.setEnabled(self.__preferences.filenameReplacement.replaceFilenameCharacters)

        # Disc Session Load Session
        self.lineEdit_DiscSessionAutomaticSessionsFolder.setEnabled(self.__preferences.discSession.autoDiscSessions)
        self.lineEdit_DiscSessionAutomaticFilenamePrefix.setEnabled(self.__preferences.discSession.autoDiscSessions)

        # Auto Audio Track(s)
        self.lineEdit_AutoAudioPreferredLanguage.setEnabled(self.__preferences.autoAudioTracks.autoSelectPreferredLanguage)

        # Auto Subtitle Track(s)
        self.lineEdit_AutoSubtitlePreferredLanguage.setEnabled(self.__preferences.autoSubtitle.autoSelectPreferredLanguage)

    def Validate(self):
        """ Validate the contents of the dialog widgets.  Returns False if any of the
            widgets are invalid.  Otherwise, returns True.
        """

        notValid = False

        notValid |= (not self.Validator_HandBrakeCLI.isValid())
        notValid |= (not self.Validator_VLC.isValid())
        notValid |= (not self.Validator_LogFilename.isValid())
        notValid |= (not self.Validator_ShortLastChapter.isValid())
        notValid |= (not self.Validator_FilenameTemplates.isValid())
        notValid |= (not self.Validator_FilenameCharacterReplaceWith.isValid())
        notValid |= (not self.Validator_FilenameCharactersToReplace.isValid())
        notValid |= (not self.Validator_Presets.isValid())
        notValid |= (not self.Validator_Mixdowns.isValid())
        notValid |= (not self.Validator_DiscSessionAutomaticSessionsFolder.isValid())
        notValid |= (not self.Validator_DefaultDestination.isValid())
        notValid |= (not self.Validator_AutoAudioPreferredLanguage.isValid())
        notValid |= (not self.Validator_AutoSubtitlePreferredLanguage.isValid())

        if (notValid):
            QMessageBox.warning(self, 'Field Errors',
                'One or more fields have an error.  Please correct the error(s) and try again.')

        return (not notValid)
