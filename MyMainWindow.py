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

import datetime, os, os.path, pathlib, subprocess, sys, tempfile, xml.dom, xml.dom.minidom as minidom

# import time
from collections import (
    deque,
    namedtuple
)

sys.path.insert(0, '../Helpers')
sys.path.insert(0, '../DiscData')

# from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtGui import QIcon
# from PyQt5.QtGui import QString
from PyQt5.QtCore import (
    Qt,
    QFileInfo,
    QProcess,
    QSettings,
    QThread
    )
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QTableWidgetItem,
    QWidget
    )

from mainwindowui import Ui_MainWindow
from PreferencesDialog import PreferencesDialog
from PyQt5WidgetDataConnectors import (
    WidgetDataConnectors,
    QCheckBoxDataConnector,
    QComboBoxDataConnector,
    QLineEditDataConnector,
    QPlainTextEditDataConnector,
    QRadioButtonGroupDataConnector,
    QSpinBoxDataConnector,
    QTableWidgetItemDataConnector
    )

from PyQt5OverrideCursor import QWaitCursor
from PyQt5Helpers import (
    AddItemToTableWidgetCell,
    TranslateProcessError
    )
from PyQt5RecentFiles import QRecentFiles
from PyQt5Validators import (WidgetValidatorList,
    QComboBox_NotEmpty_Validator,
    QLineEdit_FolderExists_Validator,
    QLineEdit_NotBlank_Validator
    )
from PyQt5SpinBoxDelegate import SpinBoxDelegate

from AppInit import __TESTING_DO_NOT_SAVE_SESSION__
from AudioTrackStates import (
    AudioTrackState,
    AudioTrackStates,
    DiscMixdownsSingleton
    )
from AudioTrackWidgets import (
    AudioTrackWidgets,
    AudioTrackWidgetsList
    )
from ChapterRanges import ChapterRanges
from Chapters import Chapters
from CropWidgets import CropWidgets
from Disc import (
    Disc,
    DiscFilenameTemplatesSingleton,
    DiscPresetsSingleton
    )
from Preferences import FilenameTemplates
from ResultsHtml import ResultsHtml
from SingletonLog import SingletonLog
from SubtitleTrackStates import SubtitleTrackState
from SubtitleTrackWidgets import (
    SubtitleTrackWidgets,
    SubtitleTrackWidgetsList
    )
from Titles import (
    Titles,
    TitleVisibleSingleton
    )
from Exceptions import UserDoNotContinueException

from Helpers import GetFolderVolumeLabel
from PyHelpers import (
    NormalizeFileName,
    TimedeltaToString,
    TemporaryFilesList
    )

VerticalHeadersVisible = namedtuple('VerticalHeadersVisible', ['firstVisualIndex',
    'lastVisualIndex', 'currentRowVisualIndex'])

def BoolToQtChecked(arg):
    if (arg):
        return Qt.Checked
    return Qt.Unchecked

class Disc_Source_Validator(QLineEdit_FolderExists_Validator):
    """ A specialized validator for the video source QLineEdit widget.

        In addition to the source folder existing, it must have a VIDEO_TS
        subfolder.
    """

    def __init__(self, widget):
        super().__init__(widget,
            message = 'The Source field is either blank or does not point to a valid folder.')

    def isValid(self):
        """ The field is valid if:
                1) The field is not blank.
                2) The value in the field is a valid folder.
                3) The folder has a VIDEO_TS subfolder.

            If the field is not valid:
                1) Highlight the field.
                2) Display an error message
                3) Return False
        """
        if (not super().isValid()):
            return False

        if ((self._flags & self.FLAG_DISABLED_WIDGET_ALWAYS_VALID)
            and (not self._widget.isEnabled())):
            return True

        folder = os.path.join(self._widget.text(), 'VIDEO_TS')
        if (folder):
            path = pathlib.Path(folder)
            if (path.is_dir()):
                return True

        if (self._flags & self.FLAG_HIGHLIGHT_WIDGETS_WITH_ERRORS):
            self.setHighlight()

        if (self._flags & self.FLAG_SHOW_ERROR_MESSAGE):
            QMessageBox.critical(QApplication.instance().mainWindow, self._errorTitle,
                'The source folder does not have a VIDEO_TS subfolder.')

        return False

class MyMainWindow(QMainWindow, Ui_MainWindow, QRecentFiles):

    WIDGET_GROUP_DISC_AUTO_AUDIO    = 0x0001
    WIDGET_GROUP_DISC_AUTO_SUBTITLE = 0x0002
    WIDGET_GROUP_DISC_CROP          = 0x0004

    TAB_INDEX_TITLE_DETAILS  = 0
    TAB_INDEX_CHAPTERS       = 1
    TAB_INDEX_CHAPTER_RANGES = 2
    TAB_INDEX_AUDIO_TRACKS   = 3
    TAB_INDEX_SUBTITLES      = 4
    TAB_INDEX_CROPPING       = 5

    MAX_RECENT_FILES = 10

    TABLE_DISC_TITLES_SELECT_COLUMN       = 0
    TABLE_DISC_TITLES_TITLE_NUMBER_COLUMN = 1
    TABLE_DISC_TITLES_DURATION_COLUMN     = 2
    TABLE_DISC_TITLES_ASPECT_COLUMN       = 3
    TABLE_DISC_TITLES_TITLE_NAME_COLUMN   = 4

    TABLE_DISCTITLE_TITLE_HEADER_COLUMN = 0
    TABLE_DISCTITLE_TITLE_DATA_COLUMN   = 1

    TABLE_DISCTITLE_TITLE_VTS_ROW                = 0
    TABLE_DISCTITLE_TITLE_TTN_ROW                = 1
    TABLE_DISCTITLE_TITLE_CELLS_ROW              = 2
    TABLE_DISCTITLE_TITLE_BLOCKS_ROW             = 3
    TABLE_DISCTITLE_TITLE_DURATION_ROW           = 4
    TABLE_DISCTITLE_TITLE_SIZE_ROW               = 5
    TABLE_DISCTITLE_TITLE_PIXELASPECTRATIO_ROW   = 6
    TABLE_DISCTITLE_TITLE_DISPLAYASPECTRATIO_ROW = 7
    TABLE_DISCTITLE_TITLE_FRAMESPERSECOND_ROW    = 8
    TABLE_DISCTITLE_TITLE_AUTOCROP_ROW           = 9

    TABLE_DISCTITLE_EPISODES_FIRSTCHAPTER_COLUMN = 0
    TABLE_DISCTITLE_EPISODES_LASTCHAPTER_COLUMN  = 1
    TABLE_DISCTITLE_EPISODES_TITLE_COLUMN        = 2

    TABLE_DISCTITLE_CHAPTERS_CHAPTERNUMBER_COLUMN = 0
    TABLE_DISCTITLE_CHAPTERS_CELLS_COLUMN         = 1
    TABLE_DISCTITLE_CHAPTERS_DURATION_COLUMN      = 2
    TABLE_DISCTITLE_CHAPTERS_TOTALDURATION_COLUMN = 3
    TABLE_DISCTITLE_CHAPTERS_TITLE_COLUMN         = 4

    TABLE_DISCTITLE_AUDIOTRACKS_TRACKNUMBER_COLUMN = 0
    TABLE_DISCTITLE_AUDIOTRACKS_DESCRIPTION_COLUMN = 1

    TABLE_DISCTITLE_SUBTITLES_TRACKNUMBER_COLUMN = 0
    TABLE_DISCTITLE_SUBTITLES_DESCRIPTION_COLUMN = 1

    STATE_FILES_SELECTION_FILTER = 'State files (*.state.xml);;All files (*, *.*)'
    STATE_FILES_DOCUMENT_ROOT    = 'HEP'

    def __init__(self, parent=None):
        super().__init__(parent)
        QRecentFiles.__init__(self)

        self.setupUi(self)
        self.setupRecentFiles(self.menuOpen_Recent, self.onAction_Disc_Open_RecentFile, 'QHEP')

        self.widgetValidators = WidgetValidatorList()

        # self.__tabIcon_Highlight = QIcon('images/draw_ellipse_16.png')
        self.__tabIcon_Clear = QIcon()
        self.__tabIcon_Highlight = QIcon('images/diamond_16.png')

        self.__widgetDataConnectors = WidgetDataConnectors()
        self.__titleSelection_widgetDataConnectors = WidgetDataConnectors()

        self.__disc_audioTrackWidgets = AudioTrackWidgetsList(self)
        self.__disc_subtitleTrackWidgets = SubtitleTrackWidgetsList(self)
        self.__disc_cropWidgets = CropWidgets(self,
            self.spinBox_Disc_Crop_Top, self.spinBox_Disc_Crop_Bottom,
            self.spinBox_Disc_Crop_Left, self.spinBox_Disc_Crop_Right)
        self.__discTitle_audioTrackWidgets = AudioTrackWidgetsList(self)
        self.__discTitle_subtitleTrackWidgets = SubtitleTrackWidgetsList(self)
        self.__discTitle_cropWidgets = CropWidgets(self,
            self.spinBox_DiscTitle_Crop_Top, self.spinBox_DiscTitle_Crop_Bottom,
            self.spinBox_DiscTitle_Crop_Left, self.spinBox_DiscTitle_Crop_Right)

        # File menu actions
        # ======================================================================
        self.actionBrowse_for_Video.triggered.connect(self.onAction_Disc_Source_Browse)
        self.actionBrowse_for_Destination.triggered.connect(self.onAction_Disc_Destination_Browse)
        self.actionSave_Hash_Session.triggered.connect(self.onAction_Disc_Save_HashSession)
        self.actionSave_Session.triggered.connect(self.onAction_Disc_Save_Session)
        self.actionSave_Session_As.triggered.connect(self.onAction_Disc_Save_SessionAs)
        self.actionSave_Temporary_Session.triggered.connect(self.onAction_Disc_Save_TemporarySession)
        self.actionDelete_Hash_Session.triggered.connect(self.onAction_Disc_Delete_Hash_Session)
        self.actionOpen_Session.triggered.connect(self.onAction_Disc_Open_Session)
        self.actionOpen_Hash_Session.triggered.connect(self.onAction_Disc_Open_HashSession)
        self.actionPreferences.triggered.connect(self.onAction_EditPreferences)
        self.actionQuit.triggered.connect(QApplication.instance().quit)

        # Tool menu actions
        # ======================================================================
        self.action_LogFile_Clear.triggered.connect(self.onAction_LogFile_Clear)
        self.action_LogFile_Open.triggered.connect(self.onAction_LogFile_Open)
        self.action_RecentFileList_Clear.triggered.connect(self.onAction_RecentFileList_Clear)
        self.action_RecentFileList_RemoveMissingFiles.triggered.connect(self.onAction_RecentFileList_RemoveMissingFiles)

        self.__init_Disc_Fields()
        self.__init_Disc_FilenameAndNotesFields()
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_Preset, self.disc, 'preset'))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_HideShortTitles, self.disc, 'hideShortTitles'))
        self.checkBox_Disc_HideShortTitles.toggled.connect(self.onSignal_toggled_Disc_HideShortTitles)
        self.__init_Disc_AudioTracks()
        self.__init_Disc_SubtitleTracks()
        self.__init_Disc_Cropping()
        self.__init_DiscTitle_DetailWidgets()
        self.__init_MakeItSo()

        self.__disc_audioTrackWidgets.addTrackItems(AudioTrackState.AUDIO_TRACK_CHOICES)
        self.__disc_subtitleTrackWidgets.addTrackItems(SubtitleTrackState.SUBTITLE_TRACK_CHOICES)
        self.__discTitle_audioTrackWidgets.addTrackItems(AudioTrackState.AUDIO_TRACK_CHOICES)
        self.__discTitle_subtitleTrackWidgets.addTrackItems(SubtitleTrackState.SUBTITLE_TRACK_CHOICES)

        self.load_Disc_FilenameTemplates()
        self.load_Disc_Presets()
        self.load_Disc_Mixdowns()
        self.load_DiscTitle_Mixdowns()

        self.enableWidgets_HasTitle()
        self.enableWidgets_HasSelectedTitle()

    def closeEvent(self, event):
        """ Save the window geometry and state before closing.
        """
        if (self.disc.source):
            if (self.validate()):
                self.onAction_Disc_Save_Session()
            else:
                result = QMessageBox.question(self, 'Save Session?',
                    ('Validation errors were found.  Unable to save session. Do '
                    'you want to exit anyway?'))
                if (result != QMessageBox.Yes):
                    event.ignore()
                    return

        settings = QSettings()

        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('windowState', self.saveState())

        event.accept()

    def enableWidgets_HasSelectedTitle(self):
        """ Enable/disable widgets throughout the main window if at least one
            title is selected.
        """
        enableWidgets = self.hasSelectedTitle

        self.stackedWidget_MakeItSo.setEnabled(enableWidgets)

    def enableWidgets_HasTitle(self):
        """ Enable/disable widgets throughout the main window if the disc has
            at least one title.
        """
        enableWidgets = self.disc.titles.hasTitles

        self.groupBox_Disc_Notes.setEnabled(enableWidgets)
        self.groupBox_Disc_AudioTracks.setEnabled(self.disc.titles.hasAudioTrack())
        self.groupBox_Disc_SubtitleTracks.setEnabled(self.disc.titles.hasSubtitleTrack())
        self.groupBox_Disc_Crop.setEnabled(enableWidgets)
        self.frame_DiscTitle_List.setEnabled(enableWidgets)

        # Disable the individual tabs instead of the entire tab widget so the
        # user can still flip through the tabs.
        for idx in range(self.tabWidget_DiscTitle.count()):
            self.tabWidget_DiscTitle.widget(idx).setEnabled(enableWidgets)

    def enableDiscWidgets(self, enableWidgets):
        """ Enable/disable widgets throughout the main window.  Used to prevent
            changes while transcoding is running.
        """
        self.menuBar.setEnabled(enableWidgets)

        self.frame_Disc_Source.setEnabled(enableWidgets)
        self.groupBox_Disc_FileName.setEnabled(enableWidgets)
        self.groupBox_Disc_Notes.setEnabled(enableWidgets)
        self.groupBox_Processing.setEnabled(enableWidgets)
        self.groupBox_Disc_AudioTracks.setEnabled(enableWidgets)
        self.groupBox_Disc_SubtitleTracks.setEnabled(enableWidgets)
        self.groupBox_Disc_Crop.setEnabled(enableWidgets)
        self.frame_DiscTitle_List.setEnabled(enableWidgets)

        if (enableWidgets):
            self.tableWidget_Disc_Titles.setEditTriggers(QAbstractItemView.DoubleClicked
                | QAbstractItemView.SelectedClicked | QAbstractItemView.EditKeyPressed)
        else:
            self.tableWidget_Disc_Titles.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for row in range(self.tableWidget_Disc_Titles.rowCount()):
            checkBox = self.tableWidget_Disc_Titles.cellWidget(row,
                self.TABLE_DISC_TITLES_SELECT_COLUMN).findChild(QCheckBox,
                'checkBox_DiscTitle_SelectTitle')
            checkBox.setEnabled(enableWidgets)

        # Disable the individual tabs instead of the entire tab widget so the
        # user can still flip through the tabs.
        for idx in range(self.tabWidget_DiscTitle.count()):
            self.tabWidget_DiscTitle.widget(idx).setEnabled(enableWidgets)

    def getTitleRow(self, title):
        """ Return the row in the tableWidget_Disc_Titles for the title.
        """
        for row in range(self.tableWidget_Disc_Titles.rowCount()):
            rowTitle = self.tableWidget_Disc_Titles.item(row, 0).data(Qt.UserRole)
            if (title.titleNumber == rowTitle.titleNumber):
                return row

        return None

    def __init_Disc_AudioTracks(self):
        """ For the disc audio track widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """
        self.toolButton_Disc_AudioTracks_Find.clicked.connect(self.onButton_Disc_AudioTracks_Find)

        # Connect the widgets to the data items.
        # ======================================================================

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_AudioTracks_SelectTrack_First,
            self.disc.audioTrackStates[0], 'track',
            self.WIDGET_GROUP_DISC_AUTO_AUDIO))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_AudioTracks_Mixdown_First_Primary,
            self.disc.audioTrackStates[0], 'primaryMixdown',
            self.WIDGET_GROUP_DISC_AUTO_AUDIO))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_AudioTracks_Mixdown_First_Secondary,
            self.disc.audioTrackStates[0], 'secondaryMixdown',
            self.WIDGET_GROUP_DISC_AUTO_AUDIO))

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_AudioTracks_SelectTrack_Second,
            self.disc.audioTrackStates[1], 'track',
            self.WIDGET_GROUP_DISC_AUTO_AUDIO))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_AudioTracks_Mixdown_Second_Primary,
            self.disc.audioTrackStates[1], 'primaryMixdown',
            self.WIDGET_GROUP_DISC_AUTO_AUDIO))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_AudioTracks_Mixdown_Second_Secondary,
            self.disc.audioTrackStates[1], 'secondaryMixdown',
            self.WIDGET_GROUP_DISC_AUTO_AUDIO))

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_AudioTracks_SelectTrack_Third,
            self.disc.audioTrackStates[2], 'track',
            self.WIDGET_GROUP_DISC_AUTO_AUDIO))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_AudioTracks_Mixdown_Third_Primary,
            self.disc.audioTrackStates[2], 'primaryMixdown',
            self.WIDGET_GROUP_DISC_AUTO_AUDIO))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_AudioTracks_Mixdown_Third_Secondary,
            self.disc.audioTrackStates[2], 'secondaryMixdown',
            self.WIDGET_GROUP_DISC_AUTO_AUDIO))

        # Add the widgets to the list of widget rows.
        # ======================================================================
        self.__disc_audioTrackWidgets.append(AudioTrackWidgets(
            self.__disc_audioTrackWidgets, 0,
            self.comboBox_Disc_AudioTracks_SelectTrack_First,
            self.comboBox_Disc_AudioTracks_Mixdown_First_Primary,
            self.comboBox_Disc_AudioTracks_Mixdown_First_Secondary
        ))
        self.__disc_audioTrackWidgets.append(AudioTrackWidgets(
            self.__disc_audioTrackWidgets, 1,
            self.comboBox_Disc_AudioTracks_SelectTrack_Second,
            self.comboBox_Disc_AudioTracks_Mixdown_Second_Primary,
            self.comboBox_Disc_AudioTracks_Mixdown_Second_Secondary
        ))
        self.__disc_audioTrackWidgets.append(AudioTrackWidgets(
            self.__disc_audioTrackWidgets, 2,
            self.comboBox_Disc_AudioTracks_SelectTrack_Third,
            self.comboBox_Disc_AudioTracks_Mixdown_Third_Primary,
            self.comboBox_Disc_AudioTracks_Mixdown_Third_Secondary
        ))

        # Create the validators.
        # ======================================================================

    def __init_Disc_Cropping(self):
        """ For the disc cropping widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """

        self.toolButton_Disc_Crop_Find.clicked.connect(self.onButton_Disc_Cropping_Find)
        self.radioButton_Disc_Crop_Automatic.setChecked(True)   # Forces the disc cropping spin buttons to disabled.

        # Connect the widgets to the data items.
        # ======================================================================

        self.__widgetDataConnectors.append(QRadioButtonGroupDataConnector(
            [self.radioButton_Disc_Crop_Automatic, self.radioButton_Disc_Crop_Custom],
            [self.disc.customCrop.PROCESS_AUTOMATIC, self.disc.customCrop.PROCESS_CUSTOM],
            self.disc.customCrop, 'processChoice',
            self.WIDGET_GROUP_DISC_CROP))

        self.__widgetDataConnectors.append(QSpinBoxDataConnector(
            self.spinBox_Disc_Crop_Top, self.disc.customCrop, 'top',
            self.WIDGET_GROUP_DISC_CROP))
        self.__widgetDataConnectors.append(QSpinBoxDataConnector(
            self.spinBox_Disc_Crop_Bottom, self.disc.customCrop, 'bottom',
            self.WIDGET_GROUP_DISC_CROP))
        self.__widgetDataConnectors.append(QSpinBoxDataConnector(
            self.spinBox_Disc_Crop_Left, self.disc.customCrop, 'left',
            self.WIDGET_GROUP_DISC_CROP))
        self.__widgetDataConnectors.append(QSpinBoxDataConnector(
            self.spinBox_Disc_Crop_Right, self.disc.customCrop, 'right',
            self.WIDGET_GROUP_DISC_CROP))

        # Add the widgets to the list of widget rows.
        # ======================================================================
        self.__disc_subtitleTrackWidgets.append(SubtitleTrackWidgets(
            self.__disc_subtitleTrackWidgets, 0,
            self.comboBox_Disc_SubtitleTracks_SelectTrack_First,
            self.checkBox_Disc_SubtitleTracks_Forced_First,
            self.checkBox_Disc_SubtitleTracks_Burn_First,
            self.checkBox_Disc_SubtitleTracks_Default_First
        ))

        # Create the validators.
        # ======================================================================

    def __init_Disc_Fields(self):
        """ For the disc widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """

        self.pushButton_Disc_Source_Browse.clicked.connect(self.onAction_Disc_Source_Browse)
        self.pushButton_Disc_Destination_Browse.clicked.connect(self.onAction_Disc_Destination_Browse)

        self.toolButton_Disc_Source_Read.clicked.connect(self.onButton_Disc_Source_Read)
        self.toolButton_Disc_Source_Find.clicked.connect(self.onButton_Disc_Source_Find)
        # I'm sure there was a reason for this at some point, but I really can't remember why the hash would ever need to be re-calculated.
        # Oddly, the ui designer does not allow you to set the visible attribute.
        self.toolButton_Disc_UpdateHash.setVisible(False)
        self.toolButton_Disc_RunVLC.clicked.connect(self.onButton_Disc_VLC)

        # Volume labels are only available under Windows.
        # self.toolButton_Disc_GetSourceDiskLabel.setVisible(sys.platform == 'win32')
        self.toolButton_Disc_GetSourceDiskLabel.clicked.connect(self.onButton_Disc_SourceDiskLabel_Get)
        self.toolButton_Disc_EditSourceDiskLabel.clicked.connect(self.onButton_Disc_SourceDiskLabel_Edit)

        # Connect the widgets to the data items.
        # ======================================================================

        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_Disc_Source, self.disc, 'source'))
        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_Disc_Destination, self.disc, 'destination'))

        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_Disc_DiskLabel, self.disc, 'sourceLabel'))

        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_NoDVDNAV, self.disc, 'nodvdnav'))

        # Create the validators.
        # ======================================================================

        self.validator_Disc_Source = Disc_Source_Validator(self.lineEdit_Disc_Source)
        self.widgetValidators.append(self.validator_Disc_Source)
        self.validator_Disc_Destination = QLineEdit_FolderExists_Validator(self.lineEdit_Disc_Destination,
            message = 'The Destination field is either blank or does not point to a valid folder.')
        self.widgetValidators.append(self.validator_Disc_Destination)

        self.validator_Disc_DiskLabel = QLineEdit_NotBlank_Validator(self.lineEdit_Disc_DiskLabel,
            message = 'The Disc label field may not be blank.')
        self.widgetValidators.append(self.validator_Disc_DiskLabel)
        self.validator_Disc_DiskLabel.removeFlags(self.validator_Disc_DiskLabel.FLAG_DISABLED_WIDGET_ALWAYS_VALID)

    def __init_Disc_FilenameAndNotesFields(self):
        """ For the disc filename and note widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """

        self.toolButton_ResetFirstEpisode.clicked.connect(self.onButton_Disc_Reset_FirstEpisode)
        self.toolButton_ResetEpisodeNumberPrecision.clicked.connect(self.onButton_Disc_Reset_EpisodeNumberPrecision)

        # Connect the widgets to the data items.
        # ======================================================================

        self.__widgetDataConnectors.append(QLineEditDataConnector(
            self.lineEdit_Disc_Title, self.disc, 'title'))
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_Mask, self.disc, 'filenameTemplate'))

        self.__widgetDataConnectors.append(QSpinBoxDataConnector(
            self.spinBox_Disc_FirstEpisode, self.disc, 'firstEpisodeNumber'))
        self.__widgetDataConnectors.append(QSpinBoxDataConnector(
            self.spinBox_Disc_EpisodeNumberPrecision, self.disc, 'episodeNumberPrecision'))

        self.__widgetDataConnectors.append(QPlainTextEditDataConnector(
            self.plainTextEdit_Disc_Notes, self.disc, 'notes'))

        # Create the validators.
        # ======================================================================

        self.validator_Disc_Title = QLineEdit_NotBlank_Validator(self.lineEdit_Disc_Title,
            message = 'The File Name Title field must not be blank.')
        self.widgetValidators.append(self.validator_Disc_Title)
        self.validator_Disc_Mask = QComboBox_NotEmpty_Validator(self.comboBox_Disc_Mask,
            message = 'The File Name Mask field must not be blank.')
        self.widgetValidators.append(self.validator_Disc_Mask)

    def __init_Disc_SubtitleTracks(self):
        """ For the disc subtitle track widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """

        self.toolButton_Disc_SubtitleTracks_Find.clicked.connect(self.onButton_Disc_SubtitleTracks_Find)

        # Connect the widgets to the data items.
        # ======================================================================

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_SubtitleTracks_SelectTrack_First,
            self.disc.subtitleTrackStates[0], 'track',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))

        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_SubtitleTracks_Forced_First,
            self.disc.subtitleTrackStates[0], 'forced',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_SubtitleTracks_Burn_First,
            self.disc.subtitleTrackStates[0], 'burn',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_SubtitleTracks_Default_First,
            self.disc.subtitleTrackStates[0], 'default',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_SubtitleTracks_SelectTrack_Second,
            self.disc.subtitleTrackStates[1], 'track',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))

        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_SubtitleTracks_Forced_Second,
            self.disc.subtitleTrackStates[1], 'forced',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_SubtitleTracks_Burn_Second,
            self.disc.subtitleTrackStates[1], 'burn',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_SubtitleTracks_Default_Second,
            self.disc.subtitleTrackStates[1], 'default',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))

        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_SubtitleTracks_SelectTrack_Third,
            self.disc.subtitleTrackStates[1], 'track',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))

        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_SubtitleTracks_Forced_Third,
            self.disc.subtitleTrackStates[2], 'forced',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_SubtitleTracks_Burn_Third,
            self.disc.subtitleTrackStates[2], 'burn',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))
        self.__widgetDataConnectors.append(QCheckBoxDataConnector(
            self.checkBox_Disc_SubtitleTracks_Default_Third,
            self.disc.subtitleTrackStates[2], 'default',
            self.WIDGET_GROUP_DISC_AUTO_SUBTITLE))

        # Add the widgets to the list of widget rows.
        # ======================================================================
        self.__disc_subtitleTrackWidgets.append(SubtitleTrackWidgets(
            self.__disc_subtitleTrackWidgets, 0,
            self.comboBox_Disc_SubtitleTracks_SelectTrack_First,
            self.checkBox_Disc_SubtitleTracks_Forced_First,
            self.checkBox_Disc_SubtitleTracks_Burn_First,
            self.checkBox_Disc_SubtitleTracks_Default_First
        ))
        self.__disc_subtitleTrackWidgets.append(SubtitleTrackWidgets(
            self.__disc_subtitleTrackWidgets, 1,
            self.comboBox_Disc_SubtitleTracks_SelectTrack_Second,
            self.checkBox_Disc_SubtitleTracks_Forced_Second,
            self.checkBox_Disc_SubtitleTracks_Burn_Second,
            self.checkBox_Disc_SubtitleTracks_Default_Second
        ))
        self.__disc_subtitleTrackWidgets.append(SubtitleTrackWidgets(
            self.__disc_subtitleTrackWidgets, 2,
            self.comboBox_Disc_SubtitleTracks_SelectTrack_Third,
            self.checkBox_Disc_SubtitleTracks_Forced_Third,
            self.checkBox_Disc_SubtitleTracks_Burn_Third,
            self.checkBox_Disc_SubtitleTracks_Default_Third
        ))

        # Create the validators.
        # ======================================================================

    def __init_DiscTitle_DetailWidgets(self):
        """ Initialze the widgets used to display the detail information for a
            title.
        """
        # The table displaying the list of disc titles.
        # ======================================================================
        self.__standardTableWidgetInitialization(self.tableWidget_Disc_Titles,
            ['Select', 'Title #', 'Duration', 'Aspect', 'Title Name'])

        self.tableWidget_Disc_Titles.itemSelectionChanged.connect(self.onDisc_Titles_ItemSelectionChanged)
        # self.tableWidget_Disc_Titles.currentItemChanged.connect(self.onDisc_Titles_CurrentItemChanged)

        self.toolButton_DiscTitle_MoveBottom.clicked.connect(self.onButton_DiscTitle_MoveBottom)
        self.toolButton_DiscTitle_MoveDown.clicked.connect(self.onButton_DiscTitle_MoveDown)
        self.toolButton_DiscTitle_MoveTop.clicked.connect(self.onButton_DiscTitle_MoveTop)
        self.toolButton_DiscTitle_MoveUp.clicked.connect(self.onButton_DiscTitle_MoveUp)
        self.toolButton_DiscTitle_RestoreNaturalOrder.clicked.connect(self.onButton_DiscTitle_RestoreNaturalOrder)

        self.toolButton_DiscTitle_ClearSelections.clicked.connect(self.onButton_DiscTitle_ClearSelections)
        self.toolButton_Disc_Find_AudioAndSubtitleTracks.clicked.connect(self.onButton_Disc_AudioAndSubtitleTracks_Find)

        # The table displaying the detail information for the selected title.
        # ======================================================================
        row = 0
        for label in ['vts:', 'ttn:', 'cells:', 'blocks:', 'duration:', 'size:',
            'pixel aspect:', 'display aspect:', 'fps:', 'autocrop:']:
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Title, row,
                self.TABLE_DISCTITLE_TITLE_HEADER_COLUMN,
                label, textAlignment=None, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Title, row,
                self.TABLE_DISCTITLE_TITLE_DATA_COLUMN,
                '', readOnly=True)
            row += 1

        self.__standardTableWidgetInitialization(self.tableWidget_DiscTitle_Title,
            ['Track', ''])

        # The table displaying the list of audio tracks for the selected disc title.
        # ======================================================================
        self.__standardTableWidgetInitialization(self.tableWidget_DiscTitle_AudioTracks,
            [' # ', 'Audio Tracks'])

        # The table displaying the list of subtitle tracks for the selected title.
        # ======================================================================
        self.__standardTableWidgetInitialization(self.tableWidget_DiscTitle_SubtitleTracks,
            [' # ', 'Subtitle Tracks'])

        # The table displaying the list of chapters for the selected title.
        # ======================================================================
        self.toolButton_DiscTitle_Chapters_ResetFirstChapter.clicked.connect(self.onButton_DiscTitle_Chapters_ResetFirstChapter)
        self.pushButton_DiscTitle_Chapters_ImportNames.clicked.connect(self.onButton_DiscTitle_Chapters_ImportNames)
        self.pushButton_DiscTitle_Chapters_ResetNames.clicked.connect(self.onButton_DiscTitle_Chapters_ResetNames)
        self.pushButton_DiscTitle_Chapters_ExportNames.clicked.connect(self.onButton_DiscTitle_Chapters_ExportNames)
        self.pushButton_DiscTitle_Chapters_SetTitleEnd.clicked.connect(self.onButton_DiscTitle_Chapters_SetTitleEnd)

        self.radioButton_DiscTitle_Chapters_NoMarkers.clicked.connect(self.onDiscTitle_Chapters_EnableWidgets)
        self.radioButton_DiscTitle_Chapters_IncludeMarkers.clicked.connect(self.onDiscTitle_Chapters_EnableWidgets)
        self.radioButton_DiscTitle_Chapters_IncludeNames.clicked.connect(self.onDiscTitle_Chapters_EnableWidgets)

        self.__standardTableWidgetInitialization(self.tableWidget_DiscTitle_Chapters,
            ['Chapter #', 'Cells', 'Duration', 'TDuration', 'Chapter Name'])

        self.radioButton_DiscTitle_Chapters_IncludeMarkers.setChecked(True)      # Set this to enable/disable chapter controls
        self.onDiscTitle_Chapters_EnableWidgets()

        # The widgets displaying the chapter ranges and episodes for the selected title.
        # ======================================================================
        self.toolButton_DiscTitle_ChapterRange_Reset.clicked.connect(self.onButton_DiscTitle_ChapterRange_Reset)
        self.toolButton_DiscTitle_AddEpisode.clicked.connect(self.onButton_DiscTitle_AddEpisode)
        self.toolButton_DiscTitle_CopyEpisode.clicked.connect(self.onButton_DiscTitle_CopyEpisode)
        self.toolButton_DiscTitle_DeleteEpisode.clicked.connect(self.onButton_DiscTitle_DeleteEpisode)
        self.toolButton_DiscTitle_Episodes_DeleteAll.clicked.connect(self.onButton_DiscTitle_Episodes_DeleteAll)

        self.radioButton_DiscTitle_AllChapters.clicked.connect(self.onDiscTitle_ChapterRanges_EnableWidgets)
        self.radioButton_DiscTitle_ChapterRange.clicked.connect(self.onDiscTitle_ChapterRanges_EnableWidgets)
        self.radioButton_DiscTitle_Episodes.clicked.connect(self.onDiscTitle_ChapterRanges_EnableWidgets)

        self.__standardTableWidgetInitialization(self.tableWidget_DiscTitle_Episodes,
            ['First Chapter', 'Last Chapter', 'Title'])

        self.discTitle_Episodes_SpinBoxDelegate = SpinBoxDelegate()
        self.tableWidget_DiscTitle_Episodes.setItemDelegateForColumn(0, self.discTitle_Episodes_SpinBoxDelegate)
        self.tableWidget_DiscTitle_Episodes.setItemDelegateForColumn(1, self.discTitle_Episodes_SpinBoxDelegate)

        self.radioButton_DiscTitle_AllChapters.setChecked(True)      # Set this to enable/disable chapter controls
        self.onDiscTitle_ChapterRanges_EnableWidgets()

        # The widgets on the Title Audio Tracks tab.
        # ======================================================================
        self.toolButton_DiscTitle_AudioTracks_Clear.clicked.connect(self.onButton_DiscTitle_AudioTracks_Clear)
        self.toolButton_DiscTitle_AudioTracks_Find.clicked.connect(self.onButton_DiscTitle_AudioTracks_Find)

        self.radioButton_DiscTitle_AudioTracks_Default.clicked.connect(self.onDiscTitle_AudioTracks_EnableWidgets)
        self.radioButton_DiscTitle_AudioTracks_Custom.clicked.connect(self.onDiscTitle_AudioTracks_EnableWidgets)

        self.__discTitle_audioTrackWidgets.append(AudioTrackWidgets(
            self.__discTitle_audioTrackWidgets, 0,
            self.comboBox_DiscTitle_AudioTracks_SelectTrack_First,
            self.comboBox_DiscTitle_AudioTracks_Mixdown_First_Primary,
            self.comboBox_DiscTitle_AudioTracks_Mixdown_First_Secondary
        ))
        self.__discTitle_audioTrackWidgets.append(AudioTrackWidgets(
            self.__discTitle_audioTrackWidgets, 1,
            self.comboBox_DiscTitle_AudioTracks_SelectTrack_Second,
            self.comboBox_DiscTitle_AudioTracks_Mixdown_Second_Primary,
            self.comboBox_DiscTitle_AudioTracks_Mixdown_Second_Secondary
        ))
        self.__discTitle_audioTrackWidgets.append(AudioTrackWidgets(
            self.__discTitle_audioTrackWidgets, 2,
            self.comboBox_DiscTitle_AudioTracks_SelectTrack_Third,
            self.comboBox_DiscTitle_AudioTracks_Mixdown_Third_Primary,
            self.comboBox_DiscTitle_AudioTracks_Mixdown_Third_Secondary
        ))

        self.radioButton_DiscTitle_AudioTracks_Default.setChecked(True)      # Set this to enable/disable chapter controls
        self.onDiscTitle_AudioTracks_EnableWidgets()

        # The widgets on the Title Subtitle Tracks tab.
        # ======================================================================
        self.toolButton_DiscTitle_SubtitleTracks_Clear.clicked.connect(self.onButton_DiscTitle_SubtitleTracks_Clear)
        self.toolButton_DiscTitle_SubtitleTracks_Find.clicked.connect(self.onButton_DiscTitle_SubtitleTracks_Find)

        self.radioButton_DiscTitle_SubtitleTracks_Default.clicked.connect(self.onDiscTitle_SubtitleTracks_EnableWidgets)
        self.radioButton_DiscTitle_SubtitleTracks_Custom.clicked.connect(self.onDiscTitle_SubtitleTracks_EnableWidgets)

        self.__discTitle_subtitleTrackWidgets.append(SubtitleTrackWidgets(
            self.__discTitle_subtitleTrackWidgets, 0,
            self.comboBox_DiscTitle_SubtitleTracks_SelectTrack_First,
            self.checkBox_DiscTitle_SubtitleTracks_Forced_First,
            self.checkBox_DiscTitle_SubtitleTracks_Burn_First,
            self.checkBox_DiscTitle_SubtitleTracks_Default_First
        ))
        self.__discTitle_subtitleTrackWidgets.append(SubtitleTrackWidgets(
            self.__discTitle_subtitleTrackWidgets, 1,
            self.comboBox_DiscTitle_SubtitleTracks_SelectTrack_Second,
            self.checkBox_DiscTitle_SubtitleTracks_Forced_Second,
            self.checkBox_DiscTitle_SubtitleTracks_Burn_Second,
            self.checkBox_DiscTitle_SubtitleTracks_Default_Second
        ))
        self.__discTitle_subtitleTrackWidgets.append(SubtitleTrackWidgets(
            self.__discTitle_subtitleTrackWidgets, 2,
            self.comboBox_DiscTitle_SubtitleTracks_SelectTrack_Third,
            self.checkBox_DiscTitle_SubtitleTracks_Forced_Third,
            self.checkBox_DiscTitle_SubtitleTracks_Burn_Third,
            self.checkBox_DiscTitle_SubtitleTracks_Default_Third
        ))

        self.radioButton_DiscTitle_SubtitleTracks_Default.setChecked(True)      # Set this to enable/disable chapter controls
        self.onDiscTitle_SubtitleTracks_EnableWidgets()

        # The widgets on the Title Cropping tab.
        # ======================================================================
        self.toolButton_DiscTitle_Crop_Clear.clicked.connect(self.onButton_DiscTitle_Crop_Clear)
        self.toolButton_DiscTitle_Crop_Find.clicked.connect(self.onButton_DiscTitle_Crop_Find)

        self.radioButton_DiscTitle_Crop_Default.clicked.connect(self.onDiscTitle_Cropping_EnableWidgets)
        self.radioButton_DiscTitle_Crop_Automatic.clicked.connect(self.onDiscTitle_Cropping_EnableWidgets)
        self.radioButton_DiscTitle_Crop_Custom.clicked.connect(self.onDiscTitle_Cropping_EnableWidgets)

        # self.__discTitle_cropWidgets.append(SubtitleTrackWidgets(
        #     self.__discTitle_subtitleTrackWidgets, 0,
        #     self.comboBox_DiscTitle_SubtitleTracks_SelectTrack_First,
        #     self.checkBox_DiscTitle_SubtitleTracks_Forced_First,
        #     self.checkBox_DiscTitle_SubtitleTracks_Burn_First,
        #     self.checkBox_DiscTitle_SubtitleTracks_Default_First
        # ))

        self.radioButton_DiscTitle_Crop_Default.setChecked(True)      # Set this to enable/disable chapter controls
        self.onDiscTitle_Cropping_EnableWidgets()

    def __init_MakeItSo(self):
        """ Initialze the widgets used to transcode a video.
        """
        self.resultsHtml = ResultsHtml(self, self.textBrowser_MakeItSo_Results)

        self.pushButton_MakeItSo_Clear.clicked.connect(self.resultsHtml.clear)
        self.pushButton_MakeItSo_Preview.clicked.connect(self.onButton_MakeItSo_Preview)
        self.pushButton_MakeItSo_Run.clicked.connect(self.onButton_MakeItSo_Run)
        self.pushButton_MakeItSo_Stop.clicked.connect(self.onButton_MakeItSo_Stop)

        self.transcodingStartTime = None
        self.transcodingWaitCursor = None
        self.transcodingCommandsDeque = None
        self.transcodingChaptersFilenames = None
        self.transcodingLog = None
        self.transcodingProcess = None

    @property
    def disc(self):
        """ Return the disc object."""
        return QApplication.instance().disc

    @property
    def hashSessionFilename(self):
        """ Return a session file name based on the disc hash value.
        """
        return "{}.state.xml".format(self.disc.titles.hash)

    @property
    def hasSelectedTitle(self):
        """ Return True/False if at least one title is selected.
        """
        for row in range(self.tableWidget_Disc_Titles.rowCount()):
            checkBox = self.tableWidget_Disc_Titles.cellWidget(row,
                self.TABLE_DISC_TITLES_SELECT_COLUMN).findChild(QCheckBox,
                'checkBox_DiscTitle_SelectTitle')
            if (checkBox.isChecked()):
                return True

        return False

    @property
    def preferences(self):
        """ Return the preferences object."""
        return QApplication.instance().preferences

    def activeTitle(self, warnIfNone=True):
        """ Returns the currently active title.

            The active title is attached to the first cell in the
            tableWidget_DiscTitle_Title widget as UserRole data.

            If warnIfNone is True (the default) a warning message will be
            displayed when a title does not exist.
        """
        title = self.tableWidget_DiscTitle_Title.item(0, 0).data(Qt.UserRole)
        if (title is None and warnIfNone):
            QMessageBox.warning(self, 'Title Not Selected',
                'Please select a title first.')

        return title

    def load_Disc_FilenameTemplates(self):
        """ Load the filename templates QComboBox from the preferences.
        """
        text = self.comboBox_Disc_Mask.currentText()

        self.comboBox_Disc_Mask.clear()
        for filenameTemplate in self.preferences.filenameTemplates:
            self.comboBox_Disc_Mask.addItem(filenameTemplate)

        self.comboBox_Disc_Mask.setCurrentText(text)

    def load_Disc_Mixdowns(self):
        """ Load the titles mixdown ComboBoxes from the preferences.
        """
        mixdowns = ['']
        for mixdown in self.preferences.mixdowns:
            mixdowns.append(mixdown.name)
        self.__disc_audioTrackWidgets.addMixdownItems(mixdowns)

        self.groupBox_Disc_AudioTracks.updateGeometry()

    def load_Disc_Presets(self):
        """ Load the presets QComboBox from the preferences.
        """

        text = self.comboBox_Disc_Preset.currentText()

        self.comboBox_Disc_Preset.clear()
        for preset in self.preferences.presets:
            self.comboBox_Disc_Preset.addItem(preset.name)

        self.comboBox_Disc_Preset.setCurrentText(text)

    def load_DiscTitle_Mixdowns(self):
        """ Load the titles mixdown ComboBoxes from the preferences.
        """
        mixdowns = ['']
        for mixdown in self.preferences.mixdowns:
            mixdowns.append(mixdown.name)

        self.__discTitle_audioTrackWidgets.addMixdownItems(mixdowns)

        self.frame_DiscTitle_AudioTracks.updateGeometry()

    def __newEpisodeToTable(self, row, episode):
        """ Insert a new episode in the tableWidget_DiscTitle_Episodes table.

            The table row must already exist.
        """
        AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Episodes, row,
            self.TABLE_DISCTITLE_EPISODES_FIRSTCHAPTER_COLUMN,
            episode.firstChapter, data=episode)
        AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Episodes, row,
            self.TABLE_DISCTITLE_EPISODES_LASTCHAPTER_COLUMN,
            episode.lastChapter)
        AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Episodes, row,
            self.TABLE_DISCTITLE_EPISODES_TITLE_COLUMN,
            episode.title, textAlignment=None)

    def onAction_Disc_Delete_Hash_Session(self):
        """ Delete the hash session file, if it exists.
        """
        if (not len(self.disc.titles)):
            QMessageBox.warning(self, 'Missing Video',
                'Please browse for a video or open a session first.')
            return

        filename = self.hashSessionFilename
        if (self.preferences.discSession.autoDiscSessions):
            filename = self.preferences.discSession.getFullFilename(filename)

        if (os.path.exists(filename)):
            result = QMessageBox.question(self, 'Delete Hash State File?',
                'Are you sure you want to delete hash state file "{}"?'.format(filename))
            if (result != QMessageBox.Yes):
                return

            os.unlink(filename)
            self.statusBar.showMessage('Session state file "{}" deleted.'.format(filename), 15000)
        else:
            QMessageBox.information(self, 'File Not Found',
                'Hash state file "{}" was not found.'.format(filename))

    def onAction_Disc_Destination_Browse(self):
        """ Select a folder where the transcoded video files will be saved.
        """
        destinationFolder = QFileDialog.getExistingDirectory(self,
            'Select Destination Folder', self.lineEdit_Disc_Destination.text())
        if (not destinationFolder):
            return

        self.lineEdit_Disc_Destination.setText(destinationFolder)
        self.validator_Disc_Destination.clearHighlight()

    def onAction_Disc_Open_RecentFile(self):
        """ Open a session file from the recent file list.
        """
        action = self.sender()
        if action:
            filename = action.data()

            if (not os.path.exists(filename)):
                QMessageBox.critical(self, 'File Not Found',
                    'File "{}" was not found.'.format(filename))
                return

            self.__loadSession(filename)

    def onAction_Disc_Open_Session(self):
        """ Select a session file and open it.
        """
        filename, selectedFilter = QFileDialog.getOpenFileName(self,
            'Select Session File', filter=self.STATE_FILES_SELECTION_FILTER)

        if (not filename):
            return

        self.__loadSession(filename)

    def onAction_Disc_Open_HashSession(self):
        """ Select a session file and open it.
        """
        if (not len(self.disc.titles)):
            QMessageBox.warning(self, 'Missing Video',
                'Please browse for a video or open a session first.')
            return

        filename = self.hashSessionFilename
        if (self.preferences.discSession.autoDiscSessions):
            filename = self.preferences.discSession.getFullFilename(filename)
        if (not os.path.exists(filename)):
            QMessageBox.warning(self, 'File Not Found',
                'Automatic session file "{}" does not exist.'.format(filename))
            return

        self.__loadSession(filename)

    def onAction_Disc_Save_HashSession(self):
        """ Create an xml file using the disc hash.  The file will contain the
            disc information and the disc state data.
        """
        if (not len(self.disc.titles)):
            QMessageBox.warning(self, 'Missing Video',
                'Please browse for a video or open a session first.')
            return

        filename = self.hashSessionFilename
        if (self.preferences.discSession.autoDiscSessions):
            filename = self.preferences.discSession.getFullFilename(filename)

        self.__saveSession(filename)

    def onAction_Disc_Save_Session(self):
        """ Create an xml file using the current file name.  The file will
            contain the disc information and the disc state data.
        """
        if (self.currentFile):
            self.__saveSession(self.currentFile)
        else:
            self.onAction_Disc_Save_SessionAs()

    def onAction_Disc_Save_SessionAs(self):
        """ Create an xml file using a user supplied file name.  The file will
            contain the disc information and the disc state data.
        """
        dlg = QFileDialog(self, 'Save Session As', filter=self.STATE_FILES_SELECTION_FILTER)
        dlg.setDefaultSuffix('state.xml')
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setFileMode(QFileDialog.AnyFile)
        if (dlg.exec()):
            self.__saveSession(dlg.selectedFiles()[0])
        del dlg

    def onAction_Disc_Save_TemporarySession(self):
        """ Create an xml file using the user supplied file name.  The file will
            contain the disc information and the disc state data.
        """
        self.__saveSession(QApplication.instance().temporarySessionFilename)

    def onAction_Disc_Source_Browse(self):
        """ Find a video folder with containing a copy of a DVD or BluRay disc
            and read the disc with Handbrake.  Then parse the disc information.
        """
        sourceFolder = QFileDialog.getExistingDirectory(self,
            'Select Video Folder', self.lineEdit_Disc_Source.text())
        if (not sourceFolder):
            return

        self.lineEdit_Disc_Source.setText(sourceFolder)
        if (not self.validator_Disc_Source.isValid()):
            return

        self.disc.clear()
        self.disc.source = sourceFolder

        if (not self.__readSource()):
            return

        filename = self.hashSessionFilename
        if (self.preferences.discSession.autoDiscSessions):
            filename = self.preferences.discSession.getFullFilename(filename)

        if (os.path.exists(filename)):
            result = QMessageBox.question(self, 'Load Automatic Session?',
                'An automatic session file exist for this video.  Do you want to load it?')
            if (result == QMessageBox.Yes):
                self.__loadSession(filename)
                return

        self.__onNewSource()

        self.transferToWindow()

    def onAction_EditPreferences(self):
        """Edit the application preferences."""

        dlg = PreferencesDialog(self.preferences, self)
        dlg.transferToWindow()
        result = dlg.exec_()
        if (result):
            dlg.transferFromWindow()
            QApplication.instance().savePreferences()
            QApplication.instance().preferences.logging.initializeLog()

            self.load_Disc_FilenameTemplates()
            self.load_Disc_Presets()
            self.load_Disc_Mixdowns()
            self.load_DiscTitle_Mixdowns()

            DiscFilenameTemplatesSingleton().set(self.preferences.filenameTemplates)
            DiscMixdownsSingleton().set(self.preferences.mixdowns.getMixdowns())
            DiscPresetsSingleton().set(self.preferences.presets.getNames())
            TitleVisibleSingleton().minimumTitleSeconds = self.preferences.autoTitle.minimumTitleSeconds

            SingletonLog().writeline('Preferences updated')
            self.statusBar.showMessage('Preferences updated.', 15000)
            QApplication.beep()

    def onAction_LogFile_Clear(self):
        """ Empty the log file.
        """
        SingletonLog().clear()
        self.statusBar.showMessage('Log file cleared.', 15000)
        QApplication.beep()

    def onAction_LogFile_Open(self):
        """ Open the log file.
        """
        SingletonLog().view()

    def onAction_RecentFileList_Clear(self):
        """ Remove all files from the recent file list.
        """
        self.clearRecentFiles()
        self.statusBar.showMessage('Recent file list updated.', 15000)
        QApplication.beep()

    def onAction_RecentFileList_RemoveMissingFiles(self):
        """ Remove files that don't exist from the recent file list.
        """
        self.removeDeadRecentFiles()
        self.statusBar.showMessage('Recent file list updated.', 15000)
        QApplication.beep()

    def onButton_Disc_AudioTracks_Find(self):
        """ Find the audio track and mixdown settings for the first visible,
            selected title.  Then set the disc audio track states and update the
            widgets.

            Use the default title is nothing matches.
        """
        self.__titleSelection_widgetDataConnectors.transferFromWidgets()

        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        if (len(matchingTitles.matchingTitles)):
            matchingTitle = matchingTitles.matchingTitles[0]
        else:
            matchingTitle = matchingTitles.defaultTitle

        self.disc.audioTrackStates.autoset_From_AudioTracks(
            matchingTitle.audioTracks,
            self.preferences)

        self.transferToWindow(self.WIDGET_GROUP_DISC_AUTO_AUDIO)
        self.statusBar.showMessage('Audio track selections updated.', 15000)
        QApplication.beep()

    def onButton_Disc_AudioAndSubtitleTracks_Find(self):
        """ Find the audio track & mixdown and the subtitle track settings for
            the first visible, selected title.  Then set the disc audio track
            states and update the widgets.

            Use the default title is nothing matches.
        """
        self.__titleSelection_widgetDataConnectors.transferFromWidgets()

        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        if (len(matchingTitles.matchingTitles)):
            matchingTitle = matchingTitles.matchingTitles[0]
        else:
            matchingTitle = matchingTitles.defaultTitle

        self.disc.audioTrackStates.autoset_From_AudioTracks(
            matchingTitle.audioTracks,
            self.preferences)
        self.disc.subtitleTrackStates.autoset_From_SubtitleTracks(
            matchingTitle.subtitleTracks,
            self.preferences)

        self.transferToWindow(self.WIDGET_GROUP_DISC_AUTO_AUDIO)
        self.transferToWindow(self.WIDGET_GROUP_DISC_AUTO_SUBTITLE)
        self.statusBar.showMessage('Audio and subtitle track selections updated.', 15000)
        QApplication.beep()

    def onButton_Disc_Cropping_Find(self):
        """ Find the cropping values for the first selected title. Then set the
            disc cropping values and update the widgets.

            Use the default title is nothing matches.
        """
        self.__titleSelection_widgetDataConnectors.transferFromWidgets()

        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        if (len(matchingTitles.matchingTitles)):
            matchingTitle = matchingTitles.matchingTitles[0]
        else:
            matchingTitle = matchingTitles.defaultTitle

        self.disc.customCrop.copy(matchingTitle.autoCrop)
        self.disc.customCrop.processChoice = self.disc.customCrop.PROCESS_CUSTOM

        self.transferToWindow(self.WIDGET_GROUP_DISC_CROP)
        self.statusBar.showMessage('Cropping selections updated.', 15000)
        QApplication.beep()

    def onButton_Disc_Reset_EpisodeNumberPrecision(self):
        """ Reset the first episode number precision to it's default value.
        """
        self.spinBox_Disc_EpisodeNumberPrecision.setValue(self.disc.DEFAULT_EPISODE_NUMBER_PRECISION)

    def onButton_Disc_Reset_FirstEpisode(self):
        """ Reset the first episode number to it's default value.
        """
        self.spinBox_Disc_FirstEpisode.setValue(self.disc.DEFAULT_FIRST_EPISODE_NUMBER)

    def onButton_Disc_Source_Find(self):
        """ Find a video folder with containing a copy of a DVD or BluRay disc.
            DO NOT read the disc with Handbrake.  DO NOT parse the disc information.
        """
        sourceFolder = QFileDialog.getExistingDirectory(self,
            'Find Video Folder', self.lineEdit_Disc_Source.text())
        if (not sourceFolder):
            return

        self.lineEdit_Disc_Source.setText(sourceFolder)
        self.lineEdit_Disc_Source.setStyleSheet('')
        self.disc.source = sourceFolder

    def onButton_Disc_Source_Read(self):
        """ Re-read the disc with Handbrake.  Then parse the disc information.
        """

        if (not self.validator_Disc_Source.isValid()):
            return

        self.disc.clear()
        if (not self.__readSource()):
            return

        filename = self.hashSessionFilename
        if (self.preferences.discSession.autoDiscSessions):
            filename = self.preferences.discSession.getFullFilename(filename)

        if (os.path.exists(filename)):
            result = QMessageBox.question(self, 'Load Automatic Session?',
                'An automatic session file exist for this video.  Do you want to load it?')
            if (result == QMessageBox.Yes):
                self.__loadSession(filename)
                return

        self.__onNewSource()
        self.disc.source = self.lineEdit_Disc_Source.text()

        self.transferToWindow()

    def onButton_Disc_SourceDiskLabel_Edit(self):
        """ Get the disk label from the user.
        """
        text, ok  = QInputDialog.getText(self, 'Set Disk Volume Label', 'Volume label',
            text = self.lineEdit_Disc_DiskLabel.text())

        if (ok):
            self.lineEdit_Disc_DiskLabel.setText(text)
            self.validator_Disc_DiskLabel.clearHighlight()

    def onButton_Disc_SourceDiskLabel_Get(self):
        """ Get the volume label for the disk where the source is located.

            Windows drives may or may not have volume labels.  If we're running
            on Windows and the drive has a volume label, use it.

            If we're not running on Windows, or if the drive does not have a
            label, look for a ".volumeLabel" file in the source folder (if
            present).  If it's not there, look for it one folder level up.
            When/if it's found, read the first line and use that as the volume
            label.
        """
        source = self.lineEdit_Disc_Source.text()
        if (not source):
            return

        volumeLabel = GetFolderVolumeLabel(source)

        self.lineEdit_Disc_DiskLabel.setText(volumeLabel)
        self.disc.sourceLabel = volumeLabel

    def onButton_Disc_SubtitleTracks_Find(self):
        """ Find the Subtitle track for the first selected title. Then set the
            disc subtitle track states and update the widgets.

            Use the default title is nothing matches.
        """
        self.__titleSelection_widgetDataConnectors.transferFromWidgets()

        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        if (len(matchingTitles.matchingTitles)):
            matchingTitle = matchingTitles.matchingTitles[0]
        else:
            matchingTitle = matchingTitles.defaultTitle

        self.disc.subtitleTrackStates.autoset_From_SubtitleTracks(
            matchingTitle.subtitleTracks,
            self.preferences)

        self.transferToWindow(self.WIDGET_GROUP_DISC_AUTO_SUBTITLE)
        self.statusBar.showMessage('Subtitle track selections updated.', 15000)
        QApplication.beep()

    def onButton_Disc_VLC(self):
        """ Start VLC using the source path.
        """
        if (not self.validator_Disc_Source.isValid()):
            return

        subprocess.Popen([self.preferences.executables.VLC,
            self.lineEdit_Disc_Source.text()],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # def onButton_Disc_VLC(self):
    #     """ Start VLC using the source path.
    #     """
    #     if (not self.validator_Disc_Source.isValid()):
    #         return
    #
    #     # process = QProcess(QApplication.instance())
    #     started = QProcess.startDetached('"{}" "{}"'.format(self.preferences.executables.VLC,
    #         self.lineEdit_Disc_Source.text()))
    #
    #     if (not started):
    #         QMessageBox.critical(self, 'Run Error',
    #             'An error has occurred while running VLC.\nVLC did not start.')
    #         return False

    def onButton_DiscTitle_AddEpisode(self):
        """ Add a chapter episode.
        """
        title = self.activeTitle()
        if (title is None):
            return

        episode = title.chapterRanges.addEpisode(title.chapters.lowestChapterNumber,
            title.chapters.highestChapterNumber, 'new episode')

        row = self.tableWidget_DiscTitle_Episodes.rowCount()
        self.tableWidget_DiscTitle_Episodes.setRowCount(row + 1)

        self.__newEpisodeToTable(row, episode)

        # If row count was zero enable the range copy/delete buttons.
        if (not row):
            self.onDiscTitle_ChapterRanges_EnableWidgets()

        self.statusBar.showMessage('1 episode added.', 15000)

    def onButton_DiscTitle_AudioTracks_Clear(self):
        """ Clear the current audio track settings for the active title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        title.audioTrackStates.clear()
        self.discTitle_AudioTrackStatesToWidgets(title)

        self.onDiscTitle_AudioTracks_EnableWidgets()

        self.statusBar.showMessage('Title audio track states cleared.', 15000)
        QApplication.beep()

    def onButton_DiscTitle_AudioTracks_Find(self):
        """ Find the current audio track settings for the active title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        title.audioTrackStates.autoset_From_AudioTracks(title.audioTracks,
            self.preferences)
        title.audioTrackStates.processChoice = title.audioTrackStates.PROCESS_CUSTOM

        self.discTitle_AudioTrackStatesToWidgets(title)
        self.onDiscTitle_AudioTracks_EnableWidgets()

        self.statusBar.showMessage('Title audio track states found and set.', 15000)
        QApplication.beep()

    def onButton_DiscTitle_ChapterRange_Reset(self):
        """ Reset the chapter ranges for the selected title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        self.spinBox_DiscTitle_ChapterRange_First.setValue(title.chapters.lowestChapterNumber)
        self.spinBox_DiscTitle_ChapterRange_Last.setValue(title.chapters.highestChapterNumber)

        self.statusBar.showMessage('Chapter ranges reset.', 15000)
        QApplication.beep()

    def onButton_DiscTitle_Chapters_ExportNames(self):
        """ Export the chapter names to a text file.
        """
        chapter = self.tableWidget_DiscTitle_Chapters.item(0, 0).data(Qt.UserRole)
        chapters = chapter.parent
        title = chapters.parent

        titleName = self.lineEdit_Disc_Title.text()
        if (titleName):
            titleName += '.chapters.txt'
        else:
            titleName = '{} Title {} Chapters.txt'.format(QApplication.instance().applicationName(), title.titleNumber)
        filename = NormalizeFileName(titleName)

        source = self.lineEdit_Disc_Source.text()
        if (source):
            chaptersFilename = os.path.join(source, filename)
        else:
            chaptersFilename = filename

        result = QFileDialog.getSaveFileName(self, 'Save Chapter Names File',
            chaptersFilename, 'Text files (*.txt);;All files (*)')

        if (not result[0]):
            return

        with open(chaptersFilename, "w") as f:
            for row in range(self.tableWidget_DiscTitle_Chapters.rowCount()):
                chapter = self.tableWidget_DiscTitle_Chapters.item(row, 0).data(Qt.UserRole)
                f.write("CHAPTER{:02d}NAME={}\n".format(chapter.chapterNumber,
                    self.tableWidget_DiscTitle_Chapters.item(row,
                    self.TABLE_DISCTITLE_CHAPTERS_TITLE_COLUMN).text()))

        self.statusBar.showMessage('Chapter names exported to {}.'.format(result[0]), 15000)
        QApplication.beep()

    def onButton_DiscTitle_Chapters_ImportNames(self):
        """ Import chapter names from a ChaptersDB.org text file.
        """
        result = QFileDialog.getOpenFileName(self, 'Open Chapter Names File',
            self.lineEdit_Disc_Source.text(), 'Text files (*.txt);;All files (*)')

        if (not result[0]):
            return

        row = 0
        with open(result[0], "r") as f:
            for line in f:

                head, tail = line.rstrip("\r\n").split("=", 1)
                if (head.endswith("NAME")):
                    self.tableWidget_DiscTitle_Chapters.item(row,
                        self.TABLE_DISCTITLE_CHAPTERS_TITLE_COLUMN).setData(Qt.EditRole, tail)
                    row += 1

        if (self.preferences.options.checkImportShortChapter):
            row = self.tableWidget_DiscTitle_Chapters.rowCount() - 1
            chapter = self.tableWidget_DiscTitle_Chapters.item(row, 0).data(Qt.UserRole)

            if (chapter.isShortChapter and chapter.isDefaultName):
                self.tableWidget_DiscTitle_Chapters.item(row,
                    self.TABLE_DISCTITLE_CHAPTERS_TITLE_COLUMN).setData(Qt.EditRole,
                    self.preferences.options.textImportShortChapter)

        self.radioButton_DiscTitle_Chapters_IncludeNames.setChecked(True)
        self.onDiscTitle_Chapters_EnableWidgets()

        self.statusBar.showMessage('Chapter names imported from {}.'.format(result[0]), 15000)
        QApplication.beep()

    def onButton_DiscTitle_Chapters_ResetFirstChapter(self):
        """ Reset the first chapter number.
        """
        self.spinBox_Disc_Chapters_FirstChapter.setValue(1)

        self.statusBar.showMessage('First chapter number reset to 1.', 15000)
        QApplication.beep()

    def onButton_DiscTitle_Chapters_ResetNames(self):
        """ Reset the chapter names to their default values.
        """
        for row in range(self.tableWidget_DiscTitle_Chapters.rowCount()):
            chapter = self.tableWidget_DiscTitle_Chapters.item(row, 0).data(Qt.UserRole)
            self.tableWidget_DiscTitle_Chapters.item(row,
                self.TABLE_DISCTITLE_CHAPTERS_TITLE_COLUMN).setData(Qt.EditRole,
                chapter.defaultName)

        self.statusBar.showMessage('Chapter names reset.', 15000)

    def onButton_DiscTitle_Chapters_SetTitleEnd(self):
        """ Set the last chapter name to the preferences short title if it is a
            short title.
        """
        row = self.tableWidget_DiscTitle_Chapters.rowCount() - 1
        chapter = self.tableWidget_DiscTitle_Chapters.item(row, 0).data(Qt.UserRole)

        if (not chapter.isShortChapter):
            result = QMessageBox.question(self, 'Set Short Chapter?',
                'Chapter {} is not a short chapter.  Do you want to continue?'.format(chapter.chapterNumber))
            if (result != QMessageBox.Yes):
                return

        if (self.tableWidget_DiscTitle_Chapters.item(row,
            self.TABLE_DISCTITLE_CHAPTERS_TITLE_COLUMN).text() != chapter.defaultName):
            result = QMessageBox.question(self, 'Set Short Chapter?',
                'The name for chapter {} is not the default name.  Do you want to continue?'.format(chapter.chapterNumber))
            if (result != QMessageBox.Yes):
                return

        self.tableWidget_DiscTitle_Chapters.item(row,
            self.TABLE_DISCTITLE_CHAPTERS_TITLE_COLUMN).setData(Qt.EditRole,
            self.preferences.options.textImportShortChapter)

        self.statusBar.showMessage('The name for chapter {} was set to {}.'.format(chapter.chapterNumber,
            self.preferences.options.textImportShortChapter), 15000)
        QApplication.beep()

    def onButton_DiscTitle_ClearSelections(self):
        """ Clear the selected attribute for all of the selected titles.
        """
        for row in range(self.tableWidget_Disc_Titles.rowCount()):
            checkBox = self.tableWidget_Disc_Titles.cellWidget(row,
                self.TABLE_DISC_TITLES_SELECT_COLUMN).findChild(QCheckBox,
                'checkBox_DiscTitle_SelectTitle')
            checkBox.setChecked(False)

        self.statusBar.showMessage('Title selections cleared.', 15000)
        QApplication.beep()

    def onButton_DiscTitle_CopyEpisode(self):
        """ Copy a chapter episode.
        """
        title = self.activeTitle()
        if (title is None):
            return

        row = self.tableWidget_DiscTitle_Episodes.currentRow()
        if (row < 0):
            QMessageBox.warning(self, 'Episode Not Selected',
                'Please select an episode first.')
            return

        episode = title.chapterRanges.addEpisode(
            self.tableWidget_DiscTitle_Episodes.item(row,
                self.TABLE_DISCTITLE_EPISODES_FIRSTCHAPTER_COLUMN).data(Qt.EditRole),
            self.tableWidget_DiscTitle_Episodes.item(row,
                self.TABLE_DISCTITLE_EPISODES_LASTCHAPTER_COLUMN).data(Qt.EditRole),
            self.tableWidget_DiscTitle_Episodes.item(row,
                self.TABLE_DISCTITLE_EPISODES_TITLE_COLUMN).text()
        )

        row = self.tableWidget_DiscTitle_Episodes.rowCount()
        self.tableWidget_DiscTitle_Episodes.setRowCount(row + 1)

        self.__newEpisodeToTable(row, episode)

        self.statusBar.showMessage('1 episode copied.', 15000)

    def onButton_DiscTitle_Crop_Clear(self):
        """ Clear the current crop settings for the active title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        title.customCrop.clear()
        self.discTitle_CropStatesToWidgets(title)
        self.onDiscTitle_Cropping_EnableWidgets()

        self.statusBar.showMessage('Title cropping states cleared.', 15000)
        QApplication.beep()

    def onButton_DiscTitle_Crop_Find(self):
        """ Clear the current audio track settings for the active title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        title.customCrop.copy(title.autoCrop)
        title.customCrop.processChoice = title.customCrop.PROCESS_CUSTOM
        self.discTitle_CropStatesToWidgets(title)
        self.onDiscTitle_Cropping_EnableWidgets()

        self.statusBar.showMessage('Title cropping states found and set.', 15000)
        QApplication.beep()

    def onButton_DiscTitle_DeleteEpisode(self):
        """ Delete an episode from a titles.
        """
        title = self.activeTitle()
        if (title is None):
            return

        row = self.tableWidget_DiscTitle_Episodes.currentRow()
        if (row < 0):
            QMessageBox.warning(self, 'Episode Not Selected',
                'Please select an episode first.')
            return

        episode = self.tableWidget_DiscTitle_Episodes.item(row, 0).data(Qt.UserRole)
        title.chapterRanges.remove(episode)
        self.tableWidget_DiscTitle_Episodes.removeRow(row)

        # If row count was zero enable the range copy/delete buttons.
        if (not self.tableWidget_DiscTitle_Episodes.rowCount()):
            self.onDiscTitle_ChapterRanges_EnableWidgets()

        self.statusBar.showMessage('1 episode deleted.', 15000)

    def onButton_DiscTitle_Episodes_DeleteAll(self):
        """ Delete all the episodes for the active title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        rowCount = self.tableWidget_DiscTitle_Episodes.rowCount()

        result = QMessageBox.question(self, 'Delete All Episodes?',
            'Are you sure you want to delete all {} episodes?'.format(rowCount))
        if (result != QMessageBox.Yes):
            return

        title.chapterRanges.clearEpisodes()
        self.tableWidget_DiscTitle_Episodes.setRowCount(0)
        self.onDiscTitle_ChapterRanges_EnableWidgets()

        self.statusBar.showMessage('{} episodes deleted.'.format(rowCount), 15000)

    def onButton_DiscTitle_MoveBottom(self):
        """ Move the selected title to the top of the list.
        """
        # We don't need to worry about the "visible row" problem because the
        # row we're moving is visible and it's below all the other rows.

        self.__titleSelection_widgetDataConnectors.transferFromWidgets()
        self.__titleDetailsFromWidgets()

        title = self.activeTitle()
        if (title is None):
            return

        self.disc.titles.moveBottom(title)
        self.__transferToDiscTables()
        self.tableWidget_Disc_Titles.setCurrentItem(
            self.tableWidget_Disc_Titles.item(
            self.tableWidget_Disc_Titles.rowCount() - 1,
            self.TABLE_DISC_TITLES_SELECT_COLUMN))

        self.onDisc_Titles_EnableWidgets()

    def onButton_DiscTitle_MoveDown(self):
        """ Move the selected title down one entry in the list.
        """
        self.__titleSelection_widgetDataConnectors.transferFromWidgets()
        self.__titleDetailsFromWidgets()

        title = self.activeTitle()
        if (title is None):
            return

        self.disc.titles.moveDown(title)
        self.__transferToDiscTables()

        row = self.getTitleRow(title)
        self.tableWidget_Disc_Titles.setCurrentItem(
            self.tableWidget_Disc_Titles.item(row,
            self.TABLE_DISC_TITLES_SELECT_COLUMN))

        self.onDisc_Titles_EnableWidgets()

    def onButton_DiscTitle_MoveTop(self):
        """ Move the selected title to the top of the list.
        """
        # We don't need to worry about the "visible row" problem because the
        # row we're moving is visible and it's above all the other rows.

        self.__titleSelection_widgetDataConnectors.transferFromWidgets()
        self.__titleDetailsFromWidgets()

        title = self.activeTitle()
        if (title is None):
            return

        self.disc.titles.moveTop(title)
        self.__transferToDiscTables()
        self.tableWidget_Disc_Titles.setCurrentItem(
            self.tableWidget_Disc_Titles.item(0,
            self.TABLE_DISC_TITLES_SELECT_COLUMN))

        self.onDisc_Titles_EnableWidgets()

    def onButton_DiscTitle_MoveUp(self):
        """ Move the selected title up one entry in the list.
        """
        self.__titleSelection_widgetDataConnectors.transferFromWidgets()
        self.__titleDetailsFromWidgets()

        title = self.activeTitle()
        if (title is None):
            return

        self.disc.titles.moveUp(title)
        self.__transferToDiscTables()

        row = self.getTitleRow(title)
        self.tableWidget_Disc_Titles.setCurrentItem(
            self.tableWidget_Disc_Titles.item(row,
            self.TABLE_DISC_TITLES_SELECT_COLUMN))

        self.onDisc_Titles_EnableWidgets()

    def onButton_DiscTitle_RestoreNaturalOrder(self):
        """ Restore the natural order of the title list.
        """
        self.__titleSelection_widgetDataConnectors.transferFromWidgets()
        self.__titleDetailsFromWidgets()

        self.disc.titles.setNaturalTitleOrder()
        self.__transferToDiscTables()

        self.tableWidget_Disc_Titles.setCurrentItem(
            self.tableWidget_Disc_Titles.item(0,
            self.TABLE_DISC_TITLES_SELECT_COLUMN))

        self.onDisc_Titles_EnableWidgets()

    def onButton_DiscTitle_SubtitleTracks_Clear(self):
        """ Clear the current subtitle track settings for the active title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        title.subtitleTrackStates.clear()
        self.discTitle_SubtitleTrackStatesToWidgets(title)
        self.onDiscTitle_SubtitleTracks_EnableWidgets()

        self.statusBar.showMessage('Title subtitle track states cleared.', 15000)
        QApplication.beep()

    def onButton_DiscTitle_SubtitleTracks_Find(self):
        """ Clear the current subtitle track settings for the active title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        title.subtitleTrackStates.autoset_From_SubtitleTracks(title.subtitleTracks,
            self.preferences)
        title.subtitleTrackStates.processChoice = title.subtitleTrackStates.PROCESS_CUSTOM

        self.discTitle_SubtitleTrackStatesToWidgets(title)
        self.onDiscTitle_SubtitleTracks_EnableWidgets()

        self.statusBar.showMessage('Title subtitle track states found and set.', 15000)
        QApplication.beep()

    def MakeCommandLineForTitle(self, title, episodeNumber, chapterRangeEpisode=None):
        """ Returns a tuple of the command line, the output file name (with path)
            and the filename of the chapter titles (may be None).

            The output file name is used to check if the file exists.
        """

        # applicationState = wx.GetApp().applicationState        # Used a lot.
        # settings = wx.GetApp().settings
        preset = self.preferences.presets.getByName(self.disc.preset)

        # Build the file name
        # ===================
        audioTags = []
        if (title.audioTrackStates.isCustom):
            audioTags = title.audioTrackStates.getMixdownTags(self.preferences.mixdowns)
        else:
            audioTags = self.disc.audioTrackStates.getMixdownTags(self.preferences.mixdowns)

        chapterRangeEpisodeTitle = ''
        if (chapterRangeEpisode is not None):
            chapterRangeEpisodeTitle = chapterRangeEpisode.title

        filename = self.preferences.filenameTemplates.buildFilename(
            self.disc.filenameTemplate,
            self.disc.title,
            preset.tag,
            audioTags,
            '{0:0{1}d}'.format(episodeNumber, self.disc.episodeNumberPrecision),
            title.title,
            chapterRangeEpisodeTitle
            )

        # Assemble the commands
        # =====================
        commands = []
        outputFilename = os.path.join(self.disc.destination, filename)

        commands.append('-i "{}"'.format(self.disc.source))
        commands.append('-o "{}"'.format(outputFilename))

        commands.append('-t {0:d}'.format(title.titleNumber))

        # Build the audio commands
        # ------------------------
        trackMixdowns = []

        tracks = []
        encoders = []
        mixdowns = []
        sampleRates = []
        bitrates = []
        dynamicRangeCompressions = []
        gains = []

        trackNames = []

        if (title.audioTrackStates.isCustom):
            for audioTrackState in title.audioTrackStates:
                if (not audioTrackState.track):
                    continue

                mixdown = self.preferences.mixdowns.getByName(audioTrackState.primaryMixdown)
                if (mixdown is not None):
                    trackMixdowns.append((audioTrackState.track, mixdown))

                mixdown = self.preferences.mixdowns.getByName(audioTrackState.secondaryMixdown)
                if (mixdown is not None):
                    trackMixdowns.append((audioTrackState.track, mixdown))
        else:
            for audioTrackState in self.disc.audioTrackStates:
                if (not audioTrackState.track):
                    continue

                mixdown = self.preferences.mixdowns.getByName(audioTrackState.primaryMixdown)
                if (mixdown is not None):
                    trackMixdowns.append((audioTrackState.track, mixdown))

                mixdown = self.preferences.mixdowns.getByName(audioTrackState.secondaryMixdown)
                if (mixdown is not None):
                    trackMixdowns.append((audioTrackState.track, mixdown))

        for track, mixdown in trackMixdowns:
            tracks.append(str(track))
            encoders.append(mixdown.encoder)
            mixdowns.append(mixdown.mixdown)
            sampleRates.append(mixdown.sampleRate)
            bitrates.append(mixdown.bitrate)
            dynamicRangeCompressions.append(mixdown.dynamicRangeCompression)
            gains.append(mixdown.gain)


        if (len(tracks) > 0):
            commands.append('-a {}'.format(','.join(tracks)))
            commands.append('-E {}'.format(','.join(encoders)))
            commands.append('-6 {}'.format(','.join(mixdowns)))
            commands.append('-R {}'.format(','.join(sampleRates)))
            commands.append('-B {}'.format(','.join(bitrates)))
            commands.append('-D {}'.format(','.join(dynamicRangeCompressions)))
            commands.append('--gain {}'.format(','.join(gains)))

        # Build the subititle commands
        # ----------------------------
        tracks = []
        forced = []
        burn = None
        default = None

        if (title.subtitleTrackStates.isCustom):
            subtitleTrackStates = title.subtitleTrackStates
        else:
            subtitleTrackStates = self.disc.subtitleTrackStates

        index = 0
        for subtitleTrackState in subtitleTrackStates:
            found = False
            if (subtitleTrackState.track):         # a.k.a. user selected
                tracks.append(subtitleTrackState.track)
                found = True

            if (found == True):
                index += 1
                if (subtitleTrackState.forced):
                    forced.append(str(index))
                if (subtitleTrackState.burn):
                    burn = str(index)
                if (subtitleTrackState.default):
                    default = str(index)

        if (len(tracks) > 0):
            commands.append('-s {}'.format(','.join(tracks)))

            if (len(forced) > 0):
                commands.append('--subtitle-forced={}'.format(','.join(forced)))
            if (burn is not None):
                commands.append('--subtitle-burned={}'.format(burn))
            if (default is not None):
                commands.append('--subtitle-default={}'.format(default))

        # nodvdnav processing
        # ----------------------

        if (self.disc.nodvdnav):
            commands.append('--no-dvdnav')

        # custom cropping processing
        # --------------------------
        cropping = None

        # Custom cropping can be done at the title level or at the application level.
        if (title.customCrop.isCustom):
            cropping = title.customCrop
        elif (title.customCrop.isDefault and self.disc.customCrop.isCustom):
            cropping = self.disc.customCrop

        if (cropping is not None):
            commands.append('--crop {}:{}:{}:{}'.format(
                cropping.top, cropping.bottom,
                cropping.left, cropping.right))

        # Chapter processing
        # ------------------
        chaptersFilename = None
        if (title.chapters.processChoice == Chapters.PROCESS_MARKERS):
            commands.append('-m')
        elif (title.chapters.processChoice == Chapters.PROCESS_NAMES):
            chaptersFile, chaptersFilename = tempfile.mkstemp(suffix='.chapters.csv', prefix='wxHEP_')

            for chapter in title.chapters:
                if (self.preferences.options.numberChapterNames):
                    line = '{},{}: {}\r\n'.format(chapter.chapterNumber,
                        chapter.chapterNumber + title.chapters.firstChapterNumber - 1,
                        chapter.title)
                else:
                    line = '{},{}\r\n'.format(chapter.chapterNumber, chapter.title)

                os.write(chaptersFile, line.encode(encoding='utf-8'))

            os.close(chaptersFile)
            commands.append('--markers="{}"'.format(chaptersFilename))

        if (title.chapterRanges.processChoice == ChapterRanges.PROCESS_RANGE):
            if (title.chapterRanges.firstChapter == title.chapterRanges.lastChapter):
                commands.append('-c {}'.format(title.chapterRanges.firstChapter))
            else:
                commands.append('-c {}-{}'.format(title.chapterRanges.firstChapter, title.chapterRanges.lastChapter))
        elif (title.chapterRanges.processChoice == title.chapterRanges.PROCESS_EPISODES and chapterRangeEpisode is not None):
            commands.append('-c {}-{}'.format(chapterRangeEpisode.firstChapter, chapterRangeEpisode.lastChapter))

        # Last but not least, the preset settings
        # ---------------------------------------
        commands.append(preset.settings)

        return (' '.join(commands), outputFilename, chaptersFilename)

    def MakeCommandLines(self, titles):
        """ Returns a tupple:

            * A list of command lines for the selected, visible titles.  The
              list will be empty if nothing is found.
            * A list chapter filenames that are created for titles with custom
              chapters names.  The list will be empty is nothing is found.
              The list is used to delete the files after all transcoding is
              complete.

            The method will check the output filename for the video.  It will
            ask the user about overwriting existing files.

            The method will always clean up any temporary files, such as chapter
            name files, before throwing any exceptions.

            WARNING: This method rasies a UserDoNotContinueException if the user
            responds with "NO" when asked 'Do you want to overwrite the
            existing file?'
        """
        commandLines = []
        outputFilenames = []
        chaptersFilenames = TemporaryFilesList()
        episodeNumber = self.disc.firstEpisodeNumber

        for title in titles:
            if (title.chapterRanges.processChoice == ChapterRanges.PROCESS_EPISODES):
                for chapterRange in title.chapterRanges:
                    commandLine, outputFilename, chaptersFilename = self.MakeCommandLineForTitle(title, episodeNumber, chapterRange)
                    commandLines.append(commandLine)
                    outputFilenames.append(outputFilename)
                    if (chaptersFilename is not None):
                        chaptersFilenames.append(chaptersFilename)
                    episodeNumber += 1
            else:
                commandLine, outputFilename, chaptersFilename = self.MakeCommandLineForTitle(title, episodeNumber)
                commandLines.append(commandLine)
                outputFilenames.append(outputFilename)
                if (chaptersFilename is not None):
                    chaptersFilenames.append(chaptersFilename)
                episodeNumber += 1

        # for outputFilename in outputFilenames:
        #     if (os.path.exists(outputFilename)):
        #
        #         result = wx.MessageBox("Warning! File '{} already exists.  Do you want to continue?".format(os.path.basename(outputFilename)),
        #             "File Already Exists", wx.YES_NO)
        #
        #         if (result == wx.NO):
        #             return

        return (commandLines, chaptersFilenames)

    def onButton_MakeItSo_Run(self):
        """ Preview the commands used to transcode each selected title.
        """
        self.transferFromWindow()

        if (not self.validate()):
            return

        matchingTitles = self.disc.titles.matchingTitles(
            Titles.FLAG_SELECTED | Titles.FLAG_VISIBLE)

        if (not len(matchingTitles.matchingTitles)):
            QMessageBox.warning(self, 'Titles Error',
                ('Error!  This video does not have any visible, selected titles.'
                '  Please select something and try again.'))
            return

        commandLines, chaptersFilenames = self.MakeCommandLines(matchingTitles.matchingTitles)

        self.transcodingStartTime = datetime.datetime.now()
        self.transcodingWaitCursor = QWaitCursor()
        self.transcodingCommandsDeque = deque(commandLines)
        # self.transcodingCommandsDeque = deque(['./TestFiles/countdown -c 20', './TestFiles/countdown -c 15', './TestFiles/countdown -c 4'])

        self.transcodingChaptersFilenames = chaptersFilenames
        self.transcodingLog = None
        if (self.preferences.logging.commandsAndTimestamps):
            self.transcodingLog = SingletonLog()

        self.statusBar.showMessage('Transcoding...')
        self.resultsHtml.appendParagraph('TRANSCODING', 'c0', self.transcodingLog)

        self.resultsHtml.appendParagraph('Transcoding start @ {}'.format(
            self.transcodingStartTime.strftime('%x %X')), 'c1',
            self.transcodingLog)

        self.enableDiscWidgets(False)
        self.stackedWidget_MakeItSo.setCurrentIndex(1)

        self.__transcode_nextTitle()

    # TODO Enhancement - on process kill, delete partial file

    def onButton_MakeItSo_Stop(self):

        self.resultsHtml.appendParagraph('Transcoding canceled by user', 'c0', self.transcodingLog)
        self.transcodingCommandsDeque.clear()
        self.transcodingProcess.kill()

        # __transcode_complete() called by onTranscoding_errorOccurred() which is triggered by kill()

    def __transcode_nextTitle(self):

        self.transcodingProcess = QProcess(QApplication.instance())
        self.transcodingProcess.errorOccurred.connect(self.onTranscoding_errorOccurred)
        self.transcodingProcess.finished.connect(self.onTranscoding_finished)
        self.transcodingProcess.readyReadStandardError.connect(self.onTranscoding_readyReadStandardError)
        self.transcodingProcess.readyReadStandardOutput.connect(self.onTranscoding_readyReadStandardOutput)
        # self.transcodingProcess.started.connect(self.onTranscoding_started)
        # self.transcodingProcess.stateChanged.connect(self.onTranscoding_stateChanged)

        command = self.transcodingCommandsDeque.popleft()

        self.trancodingTitleStartTime = datetime.datetime.now()
        self.resultsHtml.appendParagraph('Title start @ {}'.format(
            self.trancodingTitleStartTime.strftime('%x %X')), 'c2',
            self.transcodingLog)

        commandLine = '{} {}'.format(self.preferences.executables.handBrakeCLI,
            command)
        self.resultsHtml.appendParagraph(commandLine, 'c3', self.transcodingLog)
        self.transcodingProcess.start(commandLine)

    def __transcode_complete(self):

        titleStopTime = datetime.datetime.now()
        self.resultsHtml.appendParagraph(('Title finished @ {}'
            '&ensp;&ensp;&#10148;&#10148;&#10148;&ensp;&ensp;'
            'Elapsed time {}').format(titleStopTime.strftime('%x %X'),
            TimedeltaToString(titleStopTime - self.trancodingTitleStartTime)),
            'c2', self.transcodingLog)

        if (self.transcodingCommandsDeque and len(self.transcodingCommandsDeque)):
            self.__transcode_nextTitle()
            return

        self.stackedWidget_MakeItSo.setCurrentIndex(0)
        self.enableDiscWidgets(True)

        stopTime = datetime.datetime.now()
        self.resultsHtml.appendParagraph(('Transcoding finished @ {}'
            '&ensp;&ensp;&#10148;&#10148;&#10148;&ensp;&ensp;'
            'Elapsed time {}').format(stopTime.strftime('%x %X'),
            TimedeltaToString(stopTime - self.transcodingStartTime)), 'c1',
            self.transcodingLog)

        self.transcodingStartTime = None
        del self.transcodingWaitCursor
        self.transcodingWaitCursor = None
        self.transcodingCommandsDeque = None
        self.transcodingChaptersFilenames.unlink()
        self.transcodingChaptersFilenames = None
        self.transcodingLog = None
        self.transcodingProcess = None

        self.resultsHtml.appendParagraph('&nbsp;', 'c1')
        QApplication.beep()

        self.statusBar.showMessage('Transcoding finished.', 15000)

    def onButton_MakeItSo_Preview(self):
        """ Preview the commands used to transcode each selected title.
        """
        self.transferFromWindow()

        if (not self.validate()):
            return

        matchingTitles = self.disc.titles.matchingTitles(
            Titles.FLAG_SELECTED | Titles.FLAG_VISIBLE)

        if (not len(matchingTitles.matchingTitles)):
            QMessageBox.warning(self, 'Titles Error',
                ('Error!  This video does not have any visible, selected titles.'
                '  Please select something and try again.'))
            return

        log = None
        if (self.preferences.logging.commandsAndTimestamps):
            log = SingletonLog()

        self.statusBar.showMessage('Preview running...')
        self.resultsHtml.appendParagraph('PREVIEW', 'c0', log)

        with QWaitCursor():
            startTime = datetime.datetime.now()
            self.resultsHtml.appendParagraph('Encoding starting @ {}'.format(
                startTime.strftime('%x %X')), 'c1', log)

            commandLines, chaptersFilenames = self.MakeCommandLines(matchingTitles.matchingTitles)
            for commandLine in commandLines:

                titleStartTime = datetime.datetime.now()
                self.resultsHtml.appendParagraph('Title starting @ {}'.format(
                    titleStartTime.strftime('%x %X')), 'c2', log)

                self.resultsHtml.appendParagraph('{} {}'.format(self.preferences.executables.handBrakeCLI, commandLine), 'c3', log)
                # if (runCLI):
                #     app.RunHbcli(commandLine, False)
                # else:
                #     for i in range(20):
                #         wx.MilliSleep(100)
                #         wx.Yield()
                QThread.sleep(2)

                titleStopTime = datetime.datetime.now()
                self.resultsHtml.appendParagraph(('Title finished @ {}'
                    '&ensp;&ensp;&#10148;&#10148;&#10148;&ensp;&ensp;'
                    'Elapsed time {}').format(titleStopTime.strftime('%x %X'),
                    TimedeltaToString(titleStopTime - titleStartTime)), 'c2', log)

            stopTime = datetime.datetime.now()
            self.resultsHtml.appendParagraph(('Encoding finished @ {}'
                '&ensp;&ensp;&#10148;&#10148;&#10148;&ensp;&ensp;'
                'Elapsed time {}').format(stopTime.strftime('%x %X'),
                TimedeltaToString(stopTime - startTime)), 'c1', log)

            self.resultsHtml.appendParagraph('&nbsp;', 'c1')
            QApplication.beep()

        self.statusBar.showMessage('Preview complete.', 15000)

    def onTranscoding_errorOccurred(self, error):
        self.resultsHtml.appendParagraph('A process error has occured: {}'.format(
            TranslateProcessError(error)), 'c3', self.transcodingLog)

        self.__transcode_complete()

    # TODO Route preview throuch makeItSo
    # TODO about box
    # TODO Transcoding method comments

    def onTranscoding_finished(self, exitCode, exitStatus):

        if (exitCode):
            self.resultsHtml.appendParagraph(('WARNING!  Handbrake has '
                'finished with error code {}!').format(exitCode), 'c0',
                self.transcodingLog)

        if (exitStatus == QProcess.NormalExit):
            self.__transcode_complete()

    def onTranscoding_readyReadStandardError(self):
        sys.stderr.buffer.write(self.transcodingProcess.readAllStandardError())
        sys.stderr.flush()

    def onTranscoding_readyReadStandardOutput(self):
        sys.stdout.buffer.write(self.transcodingProcess.readAllStandardOutput())
        sys.stdout.flush()

    # def onTranscoding_started(self):
    #     print('onTranscoding_started')
    #
    # def onTranscoding_stateChanged(self, newState):
    #     print('onTranscoding_stateChanged', newState)

    def discTitle_AudioTrackStatesToWidgets(self, title):
        """ Transfer the title data to the title audio track state widgets on
            the Audio Tracks tab.
        """
        if (title.audioTrackStates.processChoice == title.audioTrackStates.PROCESS_DEFAULT):
            self.radioButton_DiscTitle_AudioTracks_Default.setChecked(True)
        else:
            self.radioButton_DiscTitle_AudioTracks_Custom.setChecked(True)

        self.__discTitle_audioTrackWidgets.setWidgetsFromTrackStates(title.audioTrackStates)

    def discTitle_CropStatesToWidgets(self, title):
        """ Transfer the title data to the title crop state widgets on the
            Cropping tab.
        """
        if (title.customCrop.processChoice == title.customCrop.PROCESS_DEFAULT):
            self.radioButton_DiscTitle_Crop_Default.setChecked(True)
        elif (title.customCrop.processChoice == title.customCrop.PROCESS_AUTOMATIC):
            self.radioButton_DiscTitle_Crop_Automatic.setChecked(True)
        else:
            self.radioButton_DiscTitle_Crop_Custom.setChecked(True)       # PROCESS_ALL

        self.__discTitle_cropWidgets.setWidgetsFromCrop(title.customCrop)

    def discTitle_SubtitleTrackStatesToWidgets(self, title):
        """ Transfer the title data to the title subtitle track state widgets on
            the Subtitle Tracks tab.
        """
        if (title.subtitleTrackStates.processChoice == title.subtitleTrackStates.PROCESS_DEFAULT):
            self.radioButton_DiscTitle_SubtitleTracks_Default.setChecked(True)
        else:
            self.radioButton_DiscTitle_SubtitleTracks_Custom.setChecked(True)

        self.__discTitle_subtitleTrackWidgets.setWidgetsFromTrackStates(title.subtitleTrackStates)

    def discTitle_ShowTabIcon(self, idx, hideIcon):
        """ Set/clear the icon for a disc title details tab.
        """
        if (hideIcon):
            self.tabWidget_DiscTitle.setTabIcon(idx, self.__tabIcon_Clear)
        else:
            self.tabWidget_DiscTitle.setTabIcon(idx, self.__tabIcon_Highlight)

    def onDisc_Titles_EnableWidgets(self):
        """ Enable/disable widgets associated with the disc titles list.

            Right now, this is the up/down title re-ordering buttons.
        """
        if (not self.disc.titles.hasTitles):
            frame_DiscTitle_List.setEnabled(False)
            return
        self.frame_DiscTitle_List.setEnabled(True)

        visible = self.disc_Titles_GetVerticalHeadersVisible()
        upOk = (visible.currentRowVisualIndex > visible.firstVisualIndex)
        downOk = (visible.currentRowVisualIndex < visible.lastVisualIndex)

        self.toolButton_DiscTitle_MoveTop.setEnabled(upOk)
        self.toolButton_DiscTitle_MoveUp.setEnabled(upOk)
        self.toolButton_DiscTitle_MoveDown.setEnabled(downOk)
        self.toolButton_DiscTitle_MoveBottom.setEnabled(downOk)

    def onDiscTitle_AudioTracks_EnableWidgets(self, bool=False):                # revised
        """ Enable/disable the widgets associated with custom audio track mixdowns.
        """
        title = self.activeTitle(False)
        if (title is None):
            self.tab_DiscTitle_AudioTracks.setEnabled(False)
            return

        if (not len(title.audioTracks)):
            self.tab_DiscTitle_AudioTracks.setEnabled(False)
            return

        self.tab_DiscTitle_AudioTracks.setEnabled(True)
        self.__discTitle_audioTrackWidgets.setEnabled(self.radioButton_DiscTitle_AudioTracks_Custom.isChecked())
        self.__discTitle_audioTrackWidgets.enableMixdowns()

        self.discTitle_ShowTabIcon(self.TAB_INDEX_AUDIO_TRACKS,
            self.radioButton_DiscTitle_AudioTracks_Default.isChecked())

    def onDiscTitle_ChapterRanges_EnableWidgets(self, bool=False):              # revised
        """ Enable/disable the Set Title End button.  It's only enabled if
            the Include Names button is checked and the title has chapters.
        """
        title = self.activeTitle(False)
        if (title is None):
            self.tab_DiscTitle_ChapterRanges.setEnabled(False)
            return

        rowCount = self.tableWidget_DiscTitle_Chapters.rowCount()

        self.tab_DiscTitle_ChapterRanges.setEnabled(rowCount)
        if (rowCount):
            enableRangeWidgets = self.radioButton_DiscTitle_ChapterRange.isChecked()
            self.spinBox_DiscTitle_ChapterRange_First.setEnabled(enableRangeWidgets)
            self.spinBox_DiscTitle_ChapterRange_Last.setEnabled(enableRangeWidgets)
            self.toolButton_DiscTitle_ChapterRange_Reset.setEnabled(enableRangeWidgets)

            enableEpisodesWidgets = self.radioButton_DiscTitle_Episodes.isChecked()
            self.tableWidget_DiscTitle_Episodes.setEnabled(enableEpisodesWidgets)
            self.toolButton_DiscTitle_AddEpisode.setEnabled(enableEpisodesWidgets)

            enableEpisodesWidgets2 = (enableEpisodesWidgets
                and self.tableWidget_DiscTitle_Episodes.rowCount() > 0)
            self.toolButton_DiscTitle_CopyEpisode.setEnabled(enableEpisodesWidgets2)
            self.toolButton_DiscTitle_DeleteEpisode.setEnabled(enableEpisodesWidgets2)
            self.toolButton_DiscTitle_Episodes_DeleteAll.setEnabled(enableEpisodesWidgets2)

        self.discTitle_ShowTabIcon(self.TAB_INDEX_CHAPTER_RANGES,
            self.radioButton_DiscTitle_AllChapters.isChecked())

    def onDiscTitle_Chapters_EnableWidgets(self, bool=False):                   # revised
        """ Enable/disable the widgets associated with chapter editing.
        """
        title = self.activeTitle(False)
        if (title is None):
            self.tab_DiscTitle_Chapters.setEnabled(False)
            return

        rowCount = self.tableWidget_DiscTitle_Chapters.rowCount()

        self.tab_DiscTitle_Chapters.setEnabled(rowCount)
        if (rowCount):
            enableWidgets = self.radioButton_DiscTitle_Chapters_IncludeNames.isChecked()

            self.pushButton_DiscTitle_Chapters_ExportNames.setEnabled(enableWidgets)
            self.pushButton_DiscTitle_Chapters_ResetNames.setEnabled(enableWidgets)
            self.pushButton_DiscTitle_Chapters_SetTitleEnd.setEnabled(enableWidgets)

            self.tableWidget_DiscTitle_Chapters.setEnabled(enableWidgets)

        self.discTitle_ShowTabIcon(self.TAB_INDEX_CHAPTERS,
            self.radioButton_DiscTitle_Chapters_IncludeMarkers.isChecked())

    def onDiscTitle_Cropping_EnableWidgets(self, bool=False):                   # revised
        """ Enable/disable the widgets associated with custom cropping.
        """
        title = self.activeTitle(False)
        if (title is None):
            self.tab_DiscTitle_Croping.setEnabled(False)
            return

        self.tab_DiscTitle_Croping.setEnabled(True)

        self.__discTitle_cropWidgets.setEnabled(self.radioButton_DiscTitle_Crop_Custom.isChecked())

        self.discTitle_ShowTabIcon(self.TAB_INDEX_CROPPING,
            self.radioButton_DiscTitle_Crop_Default.isChecked())

    def onDiscTitle_SubtitleTracks_EnableWidgets(self, bool=False):             # revised
        """ Enable/disable the widgets associated with custom subtitle track mixdowns.
        """
        title = self.activeTitle(False)
        if (title is None):
            self.tab_DiscTitle_SubtitleTracks.setEnabled(False)
            return

        if (not len(title.subtitleTracks)):
            self.tab_DiscTitle_SubtitleTracks.setEnabled(False)
            return

        self.tab_DiscTitle_SubtitleTracks.setEnabled(True)
        self.__discTitle_subtitleTrackWidgets.setEnabled(self.radioButton_DiscTitle_SubtitleTracks_Custom.isChecked())
        self.__discTitle_subtitleTrackWidgets.enableCheckBoxes()

        self.discTitle_ShowTabIcon(self.TAB_INDEX_SUBTITLES,
            self.radioButton_DiscTitle_SubtitleTracks_Default.isChecked())

    # def onDiscTitle_AllChapters(self, enabled):
    #     """ Enable/disable the chapter range controls in response to the all
    #         chapters radio button.
    #     """

    # def onDisc_Titles_CurrentItemChanged(self, currentItem, previousItem):
    #     """ Triggered when a new title is selected.
    #     """
    #
    #     print (currentItem, previousItem)
    #     if (currentItem):
    #         print ('current', currentItem.row())
    #     if (previousItem):
    #         print ('previous', previousItem.row())

    def onDisc_Titles_ItemSelectionChanged(self):
        """ Triggered when a new title is selected.
        """
        self.__titleDetailsFromWidgets()
        self.onDisc_Titles_EnableWidgets()

        currentItem = self.tableWidget_Disc_Titles.currentItem()
        if (currentItem is None):       # This will be None if we're here because the selected row was deleted.
            return

        title = self.tableWidget_Disc_Titles.item(currentItem.row(), 0).data(Qt.UserRole)
        self.__titleDetailsToWidgets(title)

    def disc_Titles_GetVerticalHeadersVisible(self):
        """ Returns a named tupple:
                Visual index of first visible row
                Visual index of last visible row
                Visual index of current row
        """
        firstVisibleIndex = sys.maxsize
        lastVisibleIndex = -1

        for idx in range(self.tableWidget_Disc_Titles.verticalHeader().count()):
            if (self.tableWidget_Disc_Titles.verticalHeader().isSectionHidden(idx)):
                continue

            visualIndex = self.tableWidget_Disc_Titles.verticalHeader().visualIndex(idx)

            firstVisibleIndex = min(firstVisibleIndex, visualIndex)
            lastVisibleIndex = max(lastVisibleIndex, visualIndex)

        row = self.tableWidget_Disc_Titles.currentRow()
        currentRowVisualIndex = self.tableWidget_Disc_Titles.verticalHeader().visualIndex(row)

        return VerticalHeadersVisible(firstVisibleIndex, lastVisibleIndex, currentRowVisualIndex)

    def __standardTableWidgetInitialization(self, tableWidget, horizontalHeaderLabels=None):
        """ Standard initialization for a QTableWidget.
        """
        if (horizontalHeaderLabels is not None):
            tableWidget.setHorizontalHeaderLabels(horizontalHeaderLabels)
            tableWidget.resizeColumnsToContents()
            tableWidget.horizontalHeader().setStretchLastSection(True)

        tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        tableWidget.verticalHeader().setDefaultSectionSize(21)

    def __titleDetailsToWidgets(self, title):
        """ Update the title detail widgets from the title.
        """
        # Update the title details table.
        # ======================================================================
        self.tableWidget_DiscTitle_Title.item(0, 0).setData(Qt.UserRole, title)

        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_VTS_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.vts)
        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_TTN_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.ttn)
        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_CELLS_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.cells.range)
        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_BLOCKS_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.blocks)
        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_DURATION_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.duration)
        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_SIZE_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.size.range)
        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_PIXELASPECTRATIO_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.pixelAspectRatio)
        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_DISPLAYASPECTRATIO_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.displayAspectRatio)
        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_FRAMESPERSECOND_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.framesPerSecond)
        self.tableWidget_DiscTitle_Title.item(self.TABLE_DISCTITLE_TITLE_AUTOCROP_ROW,
            self.TABLE_DISCTITLE_TITLE_DATA_COLUMN).setData(Qt.EditRole, title.autoCrop.displayString)

        # Update the title audio tracks table.
        # ======================================================================
        self.tableWidget_DiscTitle_AudioTracks.setRowCount(len(title.audioTracks))

        row = 0
        for audioTrack in title.audioTracks:
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_AudioTracks, row,
                self.TABLE_DISCTITLE_AUDIOTRACKS_TRACKNUMBER_COLUMN,
                audioTrack.trackNumber, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_AudioTracks, row,
                self.TABLE_DISCTITLE_AUDIOTRACKS_DESCRIPTION_COLUMN,
                audioTrack.description, textAlignment=None, readOnly=True)

            row += 1

        self.tableWidget_DiscTitle_AudioTracks.resizeColumnToContents(0)

        # Update the subtitle tracks table.
        # ======================================================================
        self.tableWidget_DiscTitle_SubtitleTracks.setRowCount(len(title.subtitleTracks))

        row = 0
        for subtitleTrack in title.subtitleTracks:
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_SubtitleTracks, row,
                self.TABLE_DISCTITLE_SUBTITLES_TRACKNUMBER_COLUMN,
                subtitleTrack.trackNumber, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_SubtitleTracks, row,
                self.TABLE_DISCTITLE_SUBTITLES_DESCRIPTION_COLUMN,
                subtitleTrack.description, textAlignment=None, readOnly=True)

            row += 1

        self.tableWidget_DiscTitle_SubtitleTracks.resizeColumnToContents(0)

        # Update the chapters widgets.
        # ======================================================================
        if (title.chapters.processChoice == title.chapters.PROCESS_MARKERS):
            self.radioButton_DiscTitle_Chapters_IncludeMarkers.setChecked(True)
        elif (title.chapters.processChoice == title.chapters.PROCESS_NAMES):
            self.radioButton_DiscTitle_Chapters_IncludeNames.setChecked(True)
        else:
            self.radioButton_DiscTitle_Chapters_NoMarkers.setChecked(True)

        self.spinBox_Disc_Chapters_FirstChapter.setValue(title.chapters.firstChapterNumber)

        self.tableWidget_DiscTitle_Chapters.setRowCount(len(title.chapters))
        row = 0
        for chapter in title.chapters:
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Chapters, row,
                self.TABLE_DISCTITLE_CHAPTERS_CHAPTERNUMBER_COLUMN,
                chapter.chapterNumber, data=chapter, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Chapters, row,
                self.TABLE_DISCTITLE_CHAPTERS_CELLS_COLUMN,
                chapter.cells.range, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Chapters, row,
                self.TABLE_DISCTITLE_CHAPTERS_DURATION_COLUMN,
                chapter.duration, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Chapters, row,
                self.TABLE_DISCTITLE_CHAPTERS_TOTALDURATION_COLUMN,
                chapter.cumulativeDuration, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_DiscTitle_Chapters, row,
                self.TABLE_DISCTITLE_CHAPTERS_TITLE_COLUMN,
                chapter.title, textAlignment=None)

            row += 1

        self.tableWidget_DiscTitle_Chapters.resizeColumnsToContents()

        self.onDiscTitle_Chapters_EnableWidgets()

        # Update the chapter ranges widgets.
        # ======================================================================
        if (title.chapterRanges.processChoice == title.chapterRanges.PROCESS_RANGE):
            self.radioButton_DiscTitle_ChapterRange.setChecked(True)
        elif (title.chapterRanges.processChoice == title.chapterRanges.PROCESS_EPISODES):
            self.radioButton_DiscTitle_Episodes.setChecked(True)
        else:
            self.radioButton_DiscTitle_AllChapters.setChecked(True)       # PROCESS_ALL

        self.spinBox_DiscTitle_ChapterRange_First.setMinimum(title.chapters.lowestChapterNumber)
        self.spinBox_DiscTitle_ChapterRange_Last.setMinimum(title.chapters.lowestChapterNumber)

        self.spinBox_DiscTitle_ChapterRange_First.setMaximum(title.chapters.highestChapterNumber)
        self.spinBox_DiscTitle_ChapterRange_Last.setMaximum(title.chapters.highestChapterNumber)

        if (not title.chapterRanges.firstChapter):
            self.spinBox_DiscTitle_ChapterRange_First.setValue(title.chapters.lowestChapterNumber)
        else:
            self.spinBox_DiscTitle_ChapterRange_First.setValue(title.chapterRanges.firstChapter)

        if (not title.chapterRanges.lastChapter):
            self.spinBox_DiscTitle_ChapterRange_Last.setValue(title.chapters.highestChapterNumber)
        else:
            self.spinBox_DiscTitle_ChapterRange_Last.setValue(title.chapterRanges.lastChapter)

        # This works because Python passes class objects by reference.  So, the
        # delegate for the first and second columns and this attribute are all
        # the same object.  Remember, a new spinbox is created every time a cell
        # is edited.
        self.discTitle_Episodes_SpinBoxDelegate.minimum = title.chapters.lowestChapterNumber
        self.discTitle_Episodes_SpinBoxDelegate.maximum = title.chapters.highestChapterNumber

        self.tableWidget_DiscTitle_Episodes.setRowCount(len(title.chapterRanges.episodes))
        idx = 0
        for episode in title.chapterRanges.episodes:
            self.__newEpisodeToTable(idx, episode)
            idx += 1

        self.tableWidget_DiscTitle_Episodes.resizeColumnsToContents()
        self.onDiscTitle_ChapterRanges_EnableWidgets()

        self.discTitle_AudioTrackStatesToWidgets(title)
        self.onDiscTitle_AudioTracks_EnableWidgets()

        self.discTitle_SubtitleTrackStatesToWidgets(title)
        self.onDiscTitle_SubtitleTracks_EnableWidgets()

        self.discTitle_CropStatesToWidgets(title)
        self.onDiscTitle_Cropping_EnableWidgets()

    def __titleDetailsFromWidgets(self):
        """ Update the title details from the title detail widgets.

            Only the editable items are updated.
        """
        title = self.activeTitle(False)
        if (title is None):
            return

        # Update the title chapters table.
        # ======================================================================
        if self.radioButton_DiscTitle_Chapters_IncludeMarkers.isChecked():
            title.chapters.processChoice = title.chapters.PROCESS_MARKERS
        if self.radioButton_DiscTitle_Chapters_IncludeNames.isChecked():
            title.chapters.processChoice = title.chapters.PROCESS_NAMES
        if self.radioButton_DiscTitle_Chapters_NoMarkers.isChecked():
            title.chapters.processChoice = title.chapters.PROCESS_NONE

        title.chapters.firstChapterNumber = self.spinBox_Disc_Chapters_FirstChapter.value()

        for row in range(self.tableWidget_DiscTitle_Chapters.rowCount()):
            chapter = self.tableWidget_DiscTitle_Chapters.item(row, 0).data(Qt.UserRole)
            chapter.title = self.tableWidget_DiscTitle_Chapters.item(row,
                self.TABLE_DISCTITLE_CHAPTERS_TITLE_COLUMN).data(Qt.EditRole)

        # Update the chapter ranges widgets.
        # ======================================================================
        if (self.radioButton_DiscTitle_AllChapters.isChecked()):
            title.chapterRanges.processChoice = title.chapterRanges.PROCESS_ALL
        if (self.radioButton_DiscTitle_ChapterRange.isChecked()):
            title.chapterRanges.processChoice = title.chapterRanges.PROCESS_RANGE
        if (self.radioButton_DiscTitle_Episodes.isChecked()):
            title.chapterRanges.processChoice = title.chapterRanges.PROCESS_EPISODES

        title.chapterRanges.firstChapter = self.spinBox_DiscTitle_ChapterRange_First.value()
        title.chapterRanges.lastChapter = self.spinBox_DiscTitle_ChapterRange_Last.value()

        title.chapterRanges.clearEpisodes()
        for row in range(self.tableWidget_DiscTitle_Episodes.rowCount()):
            title.chapterRanges.addEpisode(
                self.tableWidget_DiscTitle_Episodes.item(row,
                    self.TABLE_DISCTITLE_EPISODES_FIRSTCHAPTER_COLUMN).data(Qt.EditRole),
                self.tableWidget_DiscTitle_Episodes.item(row,
                    self.TABLE_DISCTITLE_EPISODES_LASTCHAPTER_COLUMN).data(Qt.EditRole),
                self.tableWidget_DiscTitle_Episodes.item(row,
                    self.TABLE_DISCTITLE_EPISODES_TITLE_COLUMN).data(Qt.EditRole)
            )

        # Update the title audio states.
        # ======================================================================
        if (self.radioButton_DiscTitle_AudioTracks_Default.isChecked()):
            title.audioTrackStates.processChoice = title.audioTrackStates.PROCESS_DEFAULT
        else:
            title.audioTrackStates.processChoice = title.audioTrackStates.PROCESS_CUSTOM

        self.__discTitle_audioTrackWidgets.setTrackStatesFromWidgets(title.audioTrackStates)

        # Update the title subtitle states.
        # ======================================================================
        if (self.radioButton_DiscTitle_SubtitleTracks_Default.isChecked()):
            title.subtitleTrackStates.processChoice = title.subtitleTrackStates.PROCESS_DEFAULT
        else:
            title.subtitleTrackStates.processChoice = title.subtitleTrackStates.PROCESS_CUSTOM

        self.__discTitle_subtitleTrackWidgets.setTrackStatesFromWidgets(title.subtitleTrackStates)

        # Update the title crop states.
        # ======================================================================

        if self.radioButton_DiscTitle_Crop_Default.isChecked():
            title.customCrop.processChoice = title.customCrop.PROCESS_DEFAULT
        elif self.radioButton_DiscTitle_Crop_Automatic.isChecked():
            title.customCrop.processChoice = title.customCrop.PROCESS_AUTOMATIC
        else:
            title.customCrop.processChoice = title.customCrop.PROCESS_CUSTOM

        self.__discTitle_cropWidgets.setCropFromWidgets(title.customCrop)

    def __onNewSource(self):
        """ Stuff to do after a new source is parsed.
        """

        self.setCurrentFile('')

        # Disc stuff
        # ======================================================================
        if (not self.lineEdit_Disc_Destination.text()):
            if (self.preferences.newSource.useDefaultDestination):
                self.lineEdit_Disc_Destination.setText(self.preferences.newSource.defaultDestination)
                self.disc.destination = self.preferences.newSource.defaultDestination

        # File Name Template
        # ======================================================================
        if (self.preferences.newSource.firstMask):
            self.comboBox_Disc_Mask.setCurrentIndex(0)

        # Processing
        # ======================================================================
        if (self.preferences.newSource.firstPreset):
            self.comboBox_Disc_Preset.setCurrentIndex(0)

        # First Selected Title or Longest Title
        # ======================================================================
        matchingTitles = self.disc.titles.matchingTitles()

        if (self.preferences.autoTitle.autoSelectLongestTitle):
            matchingTitles.longestTitle.selected = True

        self.disc.audioTrackStates.autoset_From_AudioTracks(
            matchingTitles.longestTitle.audioTracks,
            self.preferences)

        self.disc.subtitleTrackStates.autoset_From_SubtitleTracks(
            matchingTitles.longestTitle.subtitleTracks,
            self.preferences)

        if (self.preferences.autoCrop.autoCopyCrop):
            self.disc.customCrop.copy(matchingTitles.longestTitle.autoCrop)

        self.onButton_Disc_SourceDiskLabel_Get()

        self.enableWidgets_HasTitle()
        self.enableWidgets_HasSelectedTitle()
        self.__disc_audioTrackWidgets.enableMixdowns()
        self.__disc_subtitleTrackWidgets.enableCheckBoxes()

    def __loadSession(self, sessionFilename):
        """ Load the session information from a saved session file.
        """
        self.widgetValidators.clearHighlights()

        doc = minidom.parse(sessionFilename)

        if (doc.documentElement.nodeName != self.STATE_FILES_DOCUMENT_ROOT):
            raise RuntimeError('The session state file does not seem to be an HEP session file!')

        destinationOverride = None
        if (self.preferences.discSession.keepDestination):
            destinationOverride = self.lineEdit_Disc_Destination.text().strip()

        for childNode in doc.documentElement.childNodes:
            if (childNode.localName == self.disc.XMLNAME):
                self.disc.fromXML(childNode, destinationOverride)

            # elif (childNode.localName == AppState.ApplicationState.XMLName()):
            #     self.applicationState.fromXML(childNode)
            #
            # elif (childNode.localName == Titles.Titles.XMLName()):
            #     self.titles.fromXML(childNode)

        doc.unlink()

        # if (hash is not None):
        #     self.applicationState.titlesHash = hash
        #
        # if (self.applicationState.titlesHash == ""):
        #     self.applicationState.titlesHash = self.titles.getHash()
        #     self.ShowDiscHash()

        self.setCurrentFile(sessionFilename)
        self.transferToWindow()

        self.enableWidgets_HasTitle()
        self.enableWidgets_HasSelectedTitle()
        self.__disc_audioTrackWidgets.enableMixdowns()
        self.__disc_subtitleTrackWidgets.enableCheckBoxes()

        self.statusBar.showMessage('Session loaded from "{}".'.format(sessionFilename), 15000)
        QApplication.beep()

    def __readSource(self):
        """ Read the disc with Handbrake from the source with HandBrake, then
            parse the disc information.

            Returns True if the source was successfully read.
        """
        self.widgetValidators.clearHighlights()

        with QWaitCursor():
            parameters = ['-t', '0']

            if (self.checkBox_Disc_NoDVDNAV.isChecked()):
                parameters.append('--no-dvdnav')

            parameters.append('-i')
            parameters.append(self.lineEdit_Disc_Source.text())

            process = QProcess(QApplication.instance())
            process.start(self.preferences.executables.handBrakeCLI, parameters)
            # process.start(self.preferences.executables.handBrakeCLI, ['-t', '0', '-i', self.lineEdit_Disc_Source.text()])

            if (not process.waitForStarted()):
                QMessageBox.critical(self, 'Run Error',
                    'An error has occurred while running HandBrake.\nHandBrakeCLI did not start.')
                return False

            if (not process.waitForFinished()):
                QMessageBox.critical(self, 'Run Error',
                    'An error has occurred while running HandBrake.\nHandBrakeCLI did not finish.')
                return False

            # Don't know why but HandBrake returns the results on StandardError not StandardOutput (linux)
            out = bytearray(process.readAllStandardError()).decode('ISO-8859-1')

            if (self.preferences.logging.analysis):
                log = SingletonLog()
                log.writeline('{} {}'.format(self.preferences.executables.handBrakeCLI, ' '.join(parameters)))
                log.write(out)

            if (process.exitCode() != 0):
                QMessageBox.critical(self, 'Run Error',
                    ('An error has occurred while running HandBrake.\n'
                    'Exit code = {}\n{}').format(process.exitCode(), out))
                return False

            self.disc.parse(out)

            self.statusBar.showMessage('Source folder "{}" was read.'.format(self.lineEdit_Disc_Source.text()), 15000)
            return True

    def __saveSession(self, sessionFilename):
        """ Save the disc information and the disc state data to an xml file.
        """
        self.transferFromWindow()

        if (not self.validate()):
            QMessageBox.critical(self, 'Validation Errors',
                ('One or more errors were found.\n'
                'Please correct the errors and try again.\nSession was not saved.'))
            return False



        dom = minidom.getDOMImplementation()

        doc = dom.createDocument(None, self.STATE_FILES_DOCUMENT_ROOT, None)
        parentElement = doc.documentElement

        self.disc.toXML(doc, parentElement)

        if (__TESTING_DO_NOT_SAVE_SESSION__):
            self.statusBar.showMessage('TESTING!!! Session was not saved to "{}".'.format(sessionFilename), 15000)
        else:
            xmlFile = open(sessionFilename, "w")
            doc.writexml(xmlFile, "", "\t", "\n")
            xmlFile.close()

            self.statusBar.showMessage('Session saved to "{}".'.format(sessionFilename), 15000)
            QApplication.beep()


        doc.unlink()

        self.setCurrentFile(sessionFilename)

    def onSignal_toggled_Disc_HideShortTitles(self, checked):
        """ Show/hide short titles.
        """
        TitleVisibleSingleton().hideShortTitles = checked
        self.disc.titles.refreshVisible()

        firstVisibleRow = None
        for row in range(self.tableWidget_Disc_Titles.rowCount()):
            title = self.tableWidget_Disc_Titles.item(row, 0).data(Qt.UserRole)
            self.tableWidget_Disc_Titles.setRowHidden(row, not title.visible)

            if (firstVisibleRow is None and title.visible):
                firstVisibleRow = row
                self.tableWidget_Disc_Titles.setCurrentCell(row,
                    self.TABLE_DISC_TITLES_TITLE_NUMBER_COLUMN)

        self.onDisc_Titles_EnableWidgets()

    def transferFromWindow(self, groupFlags=0):
        """ Copy the data from the widgets to the data objects.
        """

        self.__widgetDataConnectors.transferFromWidgets(groupFlags)
        self.__titleSelection_widgetDataConnectors.transferFromWidgets()
        self.__titleDetailsFromWidgets()

    def __transferToDiscTables(self):
        """ Copy the data from the disc titles to the disc titles table widget.
        """

        # Transfer the disc titles to the disc titles table.
        # ======================================================================
        self.tableWidget_Disc_Titles.setRowCount(0)     # remove all existing rows
        self.tableWidget_Disc_Titles.setRowCount(len(self.disc.titles))     # add a row for each title

        titleKeys = sorted(self.disc.titles.titlesByOrderNumber.keys())
        row = 0
        self.__titleSelection_widgetDataConnectors.clear()
        for key in titleKeys:
            title = self.disc.titles.titlesByOrderNumber[key]

            item = QTableWidgetItem()
            # item.setCheckState(BoolToQtChecked(title.selected))

            widget = QWidget()
            checkBox = QCheckBox()
            checkBox.setObjectName('checkBox_DiscTitle_SelectTitle')
            checkBox.setChecked(title.selected)
            layout = QHBoxLayout(widget)
            layout.addWidget(checkBox, alignment=Qt.AlignCenter)
            layout.setContentsMargins(0,0,0,0);
            widget.setLayout(layout)
            self.tableWidget_Disc_Titles.setCellWidget(row,
                self.TABLE_DISC_TITLES_SELECT_COLUMN, widget)

            self.__titleSelection_widgetDataConnectors.append(QCheckBoxDataConnector(
                checkBox, title, 'selected', 0))

            # Add an item behind the checkbox.  It's need to generate item change signals.
            AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, row,
                self.TABLE_DISC_TITLES_SELECT_COLUMN,
                None, data=title, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, row,
                self.TABLE_DISC_TITLES_TITLE_NUMBER_COLUMN,
                title.titleNumber, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, row,
                self.TABLE_DISC_TITLES_DURATION_COLUMN,
                title.duration, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, row,
                self.TABLE_DISC_TITLES_ASPECT_COLUMN,
                title.displayAspectRatio, readOnly=True)
            item = AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, row,
                self.TABLE_DISC_TITLES_TITLE_NAME_COLUMN,
                title.title, textAlignment=None)

            self.__titleSelection_widgetDataConnectors.append(QTableWidgetItemDataConnector(
                item, title, 'title', 0))

            self.tableWidget_Disc_Titles.setRowHidden(row, not title.visible)

            row += 1

        for row in range(self.tableWidget_Disc_Titles.rowCount()):
            if (not self.tableWidget_Disc_Titles.isRowHidden(row)):
                self.tableWidget_Disc_Titles.setCurrentCell(row,
                    self.TABLE_DISC_TITLES_TITLE_NUMBER_COLUMN)
                break

    def transferToWindow(self, groupFlags=0):
        """ Copy the data from the preferences object to the dialog widgets.
        """

        self.__widgetDataConnectors.transferToWidgets(groupFlags)

        if (not groupFlags):
            self.__transferToDiscTables()

    def validate(self):
        """ Validate the fields on the main window.

            Data must be transfered from widgets to data objects first.
        """

        notValid = False

        try:
            notValid |= (not self.validator_Disc_Source.isValid())
            notValid |= (not self.validator_Disc_Destination.isValid())
            notValid |= (not self.validator_Disc_DiskLabel.isValid())
            notValid |= (not self.validator_Disc_Title.isValid())
            notValid |= (not self.validator_Disc_Mask.isValid())

            notValid |= (not self.validate_Disc_Titles())
            notValid |= (not self.validate_Disc_AudioTrackStates())
            notValid |= (not self.validate_Disc_SubtitleTrackStates())
            notValid |= (not self.validate_DiscTitles_Chapters())
            notValid |= (not self.validate_DiscTitles_ChapterRanges())
            notValid |= (not self.validate_DiscTitles_AudioTrackStates())
            notValid |= (not self.validate_DiscTitles_SubtitleTrackStates())

            notValid |= (not self.validate_Disc_FilenameTemplate())

        except UserDoNotContinueException:
            return False

        return (not notValid)

    # TODO auto save sessions.
    # TODO Validate - only loop through the title list once during validation.
    # TODO need a way to highlight/clear fields/widgets.  Clearing the error is the hard part.
    # TODO resolve data transfer, enable/disable conflict between data/widget connectors and widget collection classes like this one.
    # TODO @abstactmethod
    # TODO Window modified mechanism?
    # TODO Refactor - Create a base class for audio and subtitle track states?
    # TODO Refactor - Create a filename template class?
    # TODO add button (buttons?) in preferences dialog to reset stuff to their defaults.

    def validate_Disc_AudioTrackStates(self):
        """ Check the disc level audio track states for the following:

            * Warn the user if at least one audio track is not selected; they
              don't need need to be consecutive.  Do you want to continue?
            * Each selected (not blank) audio track must have at least one
              mixdown; they don't need to be consecutive.
            * The selected audio tracks must exist in all of the selected,
              visible titles UNLESS custom audio is selected for the title.
            * Warn the user if mixdowns are selected but a track is not.  Do you
              want to continue?

            Display an error message for each error found.  Return True/False
            if errors are found.

            WARNING: This method rasies a UserDoNotContinueException if the user
            responds with "NO" when asked 'Do you want to continue?'
        """
        selectedTrackFound = False

        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        for trackState in self.disc.audioTrackStates:
            if (trackState.isTrackSelected):
                selectedTrackFound = True
                if (not trackState.hasMixdown):
                    QMessageBox.warning(self, 'Audio Track Error',
                        ('Error!  Video audio track row #{} has an audio track '
                        'selected but does not have any mixdowns selected.'
                        '  Please fix the problem and try again.').format(
                        trackState.row))
                    return False

                for title in matchingTitles.matchingTitles:
                    # Disc level audio track settings don't apply if the title has
                    # custom audio.
                    if (title.audioTrackStates.isCustom):
                        continue

                    if (not title.audioTracks.hasTrackNumber(int(trackState.track))):
                        QMessageBox.warning(self, 'Audio Track Error',
                            ('Error!  Audio track #{} does not exist for title '
                            '#{}.'
                            '  Please fix the problem and try again.').format(
                            trackState.track, title.titleNumber))
                        return False
            else:
                if (trackState.hasMixdown):
                    result = QMessageBox.question(self, 'Audio Tracks Problem',
                        ('Warning!  Video audio track row #{} has a mixdown '
                        'selected but does not have an audio track selected.'
                        '  Do you want to continue?').format(trackState.row))
                    if (result != QMessageBox.Yes):
                        raise UserDoNotContinueException

        if (not selectedTrackFound):
            result = QMessageBox.question(self, 'Audio Tracks Problem',
                ('Warning!  This video does not have any audio tracks selected.'
                '  Do you want to continue?'))
            if (result != QMessageBox.Yes):
                raise UserDoNotContinueException

        return True

    def validate_Disc_FilenameTemplate(self):
        """ Check the filename template for the following:

            * The following template keys are always present or are checked in
              another validator (so they don't need to be checked here):

              TITLE_KEY - The title validator will make sure the title is not blank.
              PRESET_KEY - The preset combo box doesn't allow blanks or invalid presests.
              AUDIO_CODEC_KEY - The audio tag for selected mixdowns does not allow blanks.
              EPISODE_NUMBER_KEY - The episode number spin box doesn't allow blanks.

            * If the following template keys are present check all of the
              selected, visible titles:

              EPISODE_TITLE_KEY - Each title must have a title name.

              CHAPTER_RANGE_EPISODE_KEY - Each title must have chapter range
                episode processing selected.  The chapter range validator will
                make sure:
                  * At least one episode is defined.
                  * A title is present for each episode.

            Display an error message for each error found.  Return True/False
            if errors are found.
        """
        episodeTitleNeeded = (FilenameTemplates.EPISODE_TITLE_KEY in
            self.disc.filenameTemplate)
        chapterTitleNeeded = (FilenameTemplates.CHAPTER_RANGE_EPISODE_KEY in
            self.disc.filenameTemplate)

        if (not (episodeTitleNeeded or chapterTitleNeeded)):
            return True

        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        for title in matchingTitles.matchingTitles:
            if (episodeTitleNeeded and (not title.title)):
                QMessageBox.warning(self, 'Filename Template Error',
                    ('Error!  Title #{} does not have a title name but one is '
                    'required by the file name mask.'
                    '  Please fix this problem and try again.').format(
                    title.titleNumber))
                return False

            if (chapterTitleNeeded
            and title.chapterRanges.processChoice != ChapterRanges.PROCESS_EPISODES):
                QMessageBox.warning(self, 'Filename Template Error',
                    ('Error!  Title #{} does not have chapter episode processing '
                    'selected but it is required by the file name mask.'
                    '  Please fix the problem and try again.').format(
                    title.titleNumber))
                return False

        return True

    def validate_Disc_SubtitleTrackStates(self):
        """ Check the disc level subtitle track states for the following:

            * The selected subtitle tracks must exist in all of the selected,
              visible titles UNLESS custom subtitles are selected for the title.
            * Warn the user if a subtitle option is selected (forced, burn,
              default) but the subtitle is not selected (is blank).  Do you want
              to continue?

            Display an error message for each error found.  Return True/False
            if errors are found.

            WARNING: This method rasies a UserDoNotContinueException if the user
            responds with "NO" when asked 'Do you want to continue?'
        """
        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        for trackState in self.disc.subtitleTrackStates:
            if (trackState.isTrackSelected):
                for title in matchingTitles.matchingTitles:
                    # Disc level subtitle track settings don't apply if the
                    # title has custom subtitles.
                    if (title.subtitleTrackStates.isCustom):
                        continue

                    if (not title.subtitleTracks.hasTrackNumber(int(trackState.track))):
                        QMessageBox.warning(self, 'Subtitle Track Error',
                            ('Error!  Video subtitle track #{} does not exist '
                            'for title #{}.'
                            '  Please fix the problem and try again.').format(
                            trackState.track, title.titleNumber))
                        return False
            else:
                if (trackState.hasOption):
                    result = QMessageBox.question(self, 'Subtitle Tracks Problem',
                        ('Warning!  Video subtitle track row #{} has an option '
                        '(forced, burn, default) selected but does not have a '
                        'subtitle track selected.'
                        '  Do you want to continue?').format(trackState.row))
                    if (result != QMessageBox.Yes):
                        raise UserDoNotContinueException

        return True

    def validate_Disc_Titles(self):
        """ Check the titles for the following:

            * At least one visible title must exist.
            * At least one selected, visible title must exist.
            * Warn the user if one or more selected titles are not visible.  Do
              you want to continue?

            Display an error message for each error found.  Return True/False
            if errors are found.

            WARNING: This method rasies a UserDoNotContinueException if the user
            responds with "NO" when asked 'Do you want to continue?'
        """
        visibleTitleFound = False
        selectedVisibleTitleFound = False
        selectedHiddenTitleFound = False

        for title in self.disc.titles:
            if (title.visible):
                visibleTitleFound = True
                if (title.selected):
                    selectedVisibleTitleFound = True
            else:
                if (title.selected):
                    selectedHiddenTitleFound = True

        if (not visibleTitleFound):
            QMessageBox.warning(self, 'Titles Error',
                ('Error!  This video does not have any titles (at least no '
                'visible titles).  Please select another video.'))
            return False

        if (not selectedVisibleTitleFound):
            QMessageBox.warning(self, 'Titles Error',
                ('Error!  None of the visible titles for this video are '
                'selected.  Please select a title and try again.'))
            return False

        if (selectedHiddenTitleFound):
            result = QMessageBox.question(self, 'Titles Problem',
                ('Warning!  One or more selected titles are not visible.  '
                'Hidden titles will not be processed even if they are '
                'selected.'
                '  Do you want to continue?'))
            if (result != QMessageBox.Yes):
                raise UserDoNotContinueException

        return True

    def validate_DiscTitles_AudioTrackStates(self):
        """ Check the audio track states for each visible, selected video title
            that has custom audio. Check for the following:

            * Warn the user if at least one track is not selected.  Do you want
              to continue?
            * The selected audio track must exist in the title.
            * Each selected audio track must have at least one mixdown.
            * Warn the user if an audio track state has a mixdown selected but
              the audio track number is missing.  Do you want to continue?
            * Warn the user if default processing is selected but custom audio
              track states exist.  Do you want to contine?

            Display an error message for each error found.  Return True/False
            if errors are found.

            WARNING: This method rasies a UserDoNotContinueException if the user
            responds with "NO" when asked 'Do you want to continue?'
        """
        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        for title in matchingTitles.matchingTitles:
            if (not title.audioTrackStates.isCustom):
                for trackState in title.audioTrackStates:
                    if (trackState.isTrackSelected or trackState.hasMixdown):
                        result = QMessageBox.question(self, 'Custom Audio Problem',
                            ('Warning!  Title #{}, audio track row #{} has '
                            'custom audio settings but custom audio procssing '
                            'is not selected.'
                            '  Do you want to continue?').format(
                            title.titleNumber, trackState.row))
                        if (result != QMessageBox.Yes):
                            raise UserDoNotContinueException
                continue

            selectedTrackFound = False
            for trackState in title.audioTrackStates:
                if (trackState.isTrackSelected):
                    selectedTrackFound = True
                    if (not trackState.hasMixdown):
                        QMessageBox.warning(self, 'Custom Audio Error',
                            ('Error!  Title #{}, audio track row #{} has an '
                            'audio track selected but does not have any '
                            'mixdowns selected.'
                            '  Please fix the problem and try again.').format(
                            title.titleNumber, trackState.row))
                        return False

                    if (not title.audioTracks.hasTrackNumber(int(trackState.track))):
                        QMessageBox.warning(self, 'Custom Audio Error',
                            ('Error!  Audio track #{} does not exist for title '
                            '#{}.'
                            '  Please fix the problem and try again.').format(
                            trackState.track, title.titleNumber))
                        return False
                else:
                    if (trackState.hasMixdown):
                        result = QMessageBox.question(self, 'Custom Audio Problem',
                            ('Warning!  Title #{}, audio track row #{} has a '
                            'mixdown selected but does not have an audio track '
                            'selected.'
                            '  Do you want to continue?').format(
                            title.titleNumber, trackState.row))
                        if (result != QMessageBox.Yes):
                            raise UserDoNotContinueException

            if (not selectedTrackFound):
                result = QMessageBox.question(self, 'Custom Audio Problem',
                    ('Warning!  Title #{} has custom audio processing selected '
                    'but does not have any audio tracks selected.'
                    '  Do you want to continue?').format(title.titleNumber))
                if (result != QMessageBox.Yes):
                    raise UserDoNotContinueException

        return True

    def validate_DiscTitles_ChapterRanges(self):
        """ Check the chapter ranges for each visible, selected video title for the
            following:

            * If chapter range processing is selected:
              * Make sure the last chapter is greater than or equal to the first
                chapter.
            * If chapter episode processing is selected:
              * Make sure at least one episode is defined.
              * Make sure the last chapter for the episode is greater than or
                equal to the first chapter.
              * Make sure the episode has a title.
            * Warn the user if chapter episode processing is not selected but
              chapter episodes exist.  Do you want to continue?

            Display an error message for each error found.  Return True/False
            if errors are found.

            WARNING: This method rasies a UserDoNotContinueException if the user
            responds with "NO" when asked 'Do you want to continue?'
        """
        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        for title in matchingTitles.matchingTitles:
            hasEpisodes = title.chapterRanges.hasEpisodes

            if (title.chapterRanges.processChoice == title.chapterRanges.PROCESS_RANGE):
                if (title.chapterRanges.firstChapter > title.chapterRanges.lastChapter):
                    QMessageBox.warning(self, 'Chapter Range Error',(
                        'Error!  Title #{} has chapter range processing selected '
                        'but the range values are not valid.  The last chapter '
                        'must be equal to or greater than the first chapter.'
                        '  Please fix the problem and try again.').format(
                        title.titleNumber))
                    return False

            elif (title.chapterRanges.processChoice == title.chapterRanges.PROCESS_EPISODES):
                if (hasEpisodes):
                    for idx in range(len(title.chapterRanges.episodes)):
                        episode = title.chapterRanges.episodes[idx]

                        if (episode.firstChapter > episode.lastChapter):
                            QMessageBox.warning(self, 'Chapter Episodes Error',(
                                'Error!  Title #{}, episode #{} has an invalid '
                                'chapter range defined.  The last chapter must '
                                'be equal to or greater than the first chapter.'
                                '  Please fix the problem and try again.').format(
                                title.titleNumber, idx + 1))
                            return False

                        if (not episode.title):
                            QMessageBox.warning(self, 'Chapter Episodes Error',(
                                'Error!  Title #{}, episode #{} does not have a '
                                'title.'
                                '  Please fix the problem and try again.').format(
                                title.titleNumber, idx + 1))
                            return False
                else:
                    QMessageBox.warning(self, 'Chapter Episodes Error',(
                        'Error!  Title #{} has chapter episode processing '
                        'selected but the no chapter episodes are defined.'
                        '  Please fix the problem and try again.').format(
                        title.titleNumber))
                    return False

            if (hasEpisodes and
                title.chapterRanges.processChoice != title.chapterRanges.PROCESS_EPISODES):
                result = QMessageBox.question(self, 'Chapter Episodes Problem',(
                    'Warning!  Title #{} has chapter episodes but chapter '
                    'episode processing is not selected.'
                    '  Do you want to continue?').format(title.titleNumber))
                if (result != QMessageBox.Yes):
                    raise UserDoNotContinueException

        return True

    def validate_DiscTitles_Chapters(self):
        """ Check the chapters for each visible, selected video title for the
            following:

            * Warn the user if the chapter names for the title contain a mix of
              custom and default chapters.  Do you want to continue?
            * Warn the user if custom chapters processing is selected but custom
              chapters are not present.  Do you want to continue?
            * Warn the user if custom chapters are present but custom chapters
              processing is not selected.  Do you want to continue?

            Display an error message for each error found.  Return True/False
            if errors are found.

            WARNING: This method rasies a UserDoNotContinueException if the user
            responds with "NO" when asked 'Do you want to continue?'
        """
        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        for title in matchingTitles.matchingTitles:
            hasDefaultNames, hasCustomNames = title.chapters.checkChapterNames()

            if (hasDefaultNames and hasCustomNames):
                result = QMessageBox.question(self, 'Chapter Names Problem',
                    ('Warning!  Title #{} has a mix of default and custom '
                    'chapter names.'
                    '  Do you want to continue?').format(title.titleNumber))
                if (result != QMessageBox.Yes):
                    raise UserDoNotContinueException

            if (hasCustomNames and not title.chapters.isNames):
                result = QMessageBox.question(self, 'Chapter Names Problem',
                    ('Warning! Title #{} has custom chapter names defined but '
                    'chapter names processing is are not selected.'
                    '  Do you want to continue?').format(title.titleNumber))
                if (result != QMessageBox.Yes):
                    raise UserDoNotContinueException

            if (title.chapters.isNames and not hasCustomNames):
                result = QMessageBox.question(self, 'Chapter Names Problem',
                    ('Warning!  Title #{} has chapter names processing '
                    'selected but does not have custom chapter names.'
                    '  Do you want to continue?').format(title.titleNumber))
                if (result != QMessageBox.Yes):
                    raise UserDoNotContinueException

        return True

    def validate_DiscTitles_SubtitleTrackStates(self):
        """ Check the subtitle track states for each visible, selected video
            title that has custom subtitles. Check for the following:

            * Warn the user if custom subtitle options exist but custom subtitle
              processing is not selected.
            * The selected subtitle track must exist in the title.
            * Warn the user if a subtitle option is selected (forced, burn,
              default) but the subtitle is not selected (is blank).  Do you want
              to continue?

            Display an error message for each error found.  Return True/False
            if errors are found.

            WARNING: This method rasies a UserDoNotContinueException if the user
            responds with "NO" when asked 'Do you want to continue?'
        """
        matchingTitles = self.disc.titles.matchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        for title in matchingTitles.matchingTitles:
            if (not title.subtitleTrackStates.isCustom):
                for trackState in title.subtitleTrackStates:
                    if (trackState.isTrackSelected or trackState.hasOption):
                        result = QMessageBox.question(self, 'Custom Subtitle Problem',
                            ('Warning!  Title #{}, subtitle track row #{} has '
                            'custom subtitle settings but custom subtitle procssing '
                            'is not selected.'
                            '  Do you want to continue?').format(
                            title.titleNumber, trackState.row))
                        if (result != QMessageBox.Yes):
                            raise UserDoNotContinueException
                continue

            for trackState in title.subtitleTrackStates:
                if (trackState.isTrackSelected):
                    if (not title.subtitleTracks.hasTrackNumber(int(trackState.track))):
                        QMessageBox.warning(self, 'Custom Subtitle Error',
                            ('Error!  Subtitle track #{} does not exist for '
                            'title #{}.'
                            '  Please fix the problem and try again.').format(
                            trackState.track, title.titleNumber))
                        return False
                else:
                    if (trackState.hasOption):
                        result = QMessageBox.question(self, 'Custom Subtitle Problem',
                            ('Warning!  Title #{}, subtitle track row #{} has an '
                            'option (forced, burn, default) selected but does '
                            'not have a subtitle track selected.'
                            '  Do you want to continue?').format(
                            title.titleNumber, trackState.row))
                        if (result != QMessageBox.Yes):
                            raise UserDoNotContinueException
        return True

    # def validate_Disc_Source(self):
    #     """ The titles source is valid if:
    #
    #         1) The path exists.
    #         2) It is a directory.
    #     """
    #
    #     self.lineEdit_Disc_Source.setStyleSheet('')
    #
    #     folder = self.lineEdit_Disc_Source.text()
    #     if (folder):
    #         path = pathlib.Path(folder)
    #         if (path.is_dir()):
    #             return True
    #
    #     QMessageBox.critical(self, 'Source Folder',
    #         'The source folder is either blank or is not a valid folder.')
    #
    #     self.lineEdit_Disc_Source.setStyleSheet(self.PROBLEM_BACKGROUND_STYLE)
    #     return False
