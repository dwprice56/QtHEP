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

import os.path, pathlib, sys, xml.dom, xml.dom.minidom as minidom
# import time

sys.path.insert(0, '/home/dave/QtProjects/Helpers')
sys.path.insert(0, '/home/dave/QtProjects/DiscData')

# from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtGui import QIcon
# from PyQt5.QtGui import QString
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QMainWindow,
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
    QSpinBoxDataConnector
)

from PyQt5OverrideCursor import QWaitCursor
from PyQt5Helpers import (
    GetVolumeLabel,
    AddItemToTableWidgetCell
)
from PyQt5Validators import (
    QComboBox_NotEmpty_Validator,
    QLineEdit_FolderExists_Validator,
    QLineEdit_NotBlank_Validator
)
from PyQt5SpinBoxDelegate import SpinBoxDelegate

from AppInit import __TESTING_DO_NOT_SAVE_SESSION__
from AudioTrackStates import AudioTrackState
from Disc import (
    Disc,
    DiscFilenameTemplatesSingleton,
    DiscPresetsSingleton
)
from SingletonLog import SingletonLog
from SubtitleTrackStates import SubtitleTrackState
from Titles import (
    Titles,
    TitleVisibleSingleton
)
from PyHelpers import NormalizeFileName

def BoolToQtChecked(arg):
    if (arg):
        return Qt.Checked
    return Qt.Unchecked

class MyMainWindow(QMainWindow, Ui_MainWindow):

    WIDGET_GROUP_DISC_AUTO_AUDIO    = 0x0001
    WIDGET_GROUP_DISC_AUTO_SUBTITLE = 0x0002
    WIDGET_GROUP_DISC_CROP          = 0x0004

    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)

        self.highlightedTabIcon = QIcon('images/draw_ellipse_16.png')
        # self.highlightedTabIcon = QIcon('images/diamond_16.png')
        
        self.__widgetDataConnectors = WidgetDataConnectors()

        self.actionBrowse_for_Video.triggered.connect(self.onDisc_Source_Browse)
        self.actionBrowse_for_Destination.triggered.connect(self.onDisc_Destination_Browse)
        self.actionSave_Hash_Session.triggered.connect(self.onSaveHashSession)
        self.actionPreferences.triggered.connect(self.onEditPreferences)
        self.actionQuit.triggered.connect(QApplication.instance().quit)

        self.__initDiscFields()
        self.__initDiscFilenameAndNotesFields()
        self.__widgetDataConnectors.append(QComboBoxDataConnector(
            self.comboBox_Disc_Preset, self.disc, 'preset'))
        self.__initDiscAudioTracks()
        self.__initDiscSubtitleTracks()
        self.__initDiscCropping()
        self.__initDiscTitleDetailWidgets()

        self.Load_Disc_FilenameTemplates()
        self.Load_Disc_Presets()
        self.Load_Disc_MixdownTrackNumbers()
        self.Load_Disc_Mixdowns()
        self.Load_Disc_SubtitleTrackNumbers()

    def __initDiscAudioTracks(self):
        """ For the disc audio track widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """

        # TODO enable/disable this button if title count > 0
        self.toolButton_Disc_Find_AudioTracks.clicked.connect(self.onDisc_Find_AudioTracks)

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

        # Create the validators.
        # ======================================================================

        # TODO make sure all of the selected audio tracks exist in all of the selected titles.
        # TODO make sure at least on mixdown is selected

    def __initDiscCropping(self):
        """ For the disc cropping widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """

        # TODO enable/disable this button if title count > 0
        self.toolButton_Disc_Find_Crop.clicked.connect(self.onDisc_Find_Crop)
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

        # Create the validators.
        # ======================================================================

        # TODO make sure all of the selected audio tracks exist in all of the selected titles.
        # TODO make sure at least on mixdown is selected

    def __initDiscFields(self):
        """ For the disc widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """

        # TODO add "override automatic read" check box.  only enabled (visible?) if automatic disc sessions (preferences) is enabled.
        # TODO add "open hash file" menu item, tool button
        # TODO add "Save to..." submenu?

        self.pushButton_Disc_Source_Browse.clicked.connect(self.onDisc_Source_Browse)
        self.pushButton_Disc_Destination_Browse.clicked.connect(self.onDisc_Destination_Browse)

        self.toolButton_Disc_Source_Read.clicked.connect(self.onDisc_Source_Read)
        self.toolButton_Disc_Source_Find.clicked.connect(self.onDisc_Source_Find)
        # I'm sure there was a reason for this at some point, but I really can't remember why the hash would ever need to be re-calculated.
        # Oddly, the ui designer does not allow you to set the visible attribute.
        self.toolButton_Disc_UpdateHash.setVisible(False)
        self.toolButton_Disc_RunVLC.clicked.connect(self.onVLC)

        # Volume labels are only available under Windows.
        self.toolButton_Disc_GetSourceDiskLabel.setVisible(sys.platform == 'win32')
        self.toolButton_Disc_GetSourceDiskLabel.clicked.connect(self.onGetSourceDiskLabel)
        self.toolButton_Disc_EditSourceDiskLabel.clicked.connect(self.onEditSourceDiskLabel)

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

        self.Validator_Disc_Source = QLineEdit_FolderExists_Validator(self.lineEdit_Disc_Source,
            message = 'The Source field is either blank or does not point to a valid folder.')
        self.Validator_Disc_Destination = QLineEdit_FolderExists_Validator(self.lineEdit_Disc_Destination,
            message = 'The Destination field is either blank or does not point to a valid folder.')

        self.Validator_Disc_DiskLabel = QLineEdit_NotBlank_Validator(self.lineEdit_Disc_DiskLabel,
            message = 'The Disc label field may not be blank.')
        self.Validator_Disc_DiskLabel.removeFlags(self.Validator_Disc_DiskLabel.FLAG_DISABLED_WIDGET_ALWAYS_VALID)

    def __initDiscFilenameAndNotesFields(self):
        """ For the disc filename and note widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """

        self.toolButton_ResetFirstEpisode.clicked.connect(self.onDisc_Reset_FirstEpisode)
        self.toolButton_ResetEpisodeNumberPrecision.clicked.connect(self.onDisc_Reset_EpisodeNumberPrecision)

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

        self.Validator_Disc_Title = QLineEdit_NotBlank_Validator(self.lineEdit_Disc_Title,
            message = 'The File Name Title field must not be blank.')
        self.Validator_Disc_Mask = QComboBox_NotEmpty_Validator(self.comboBox_Disc_Mask,
            message = 'The File Name Mask field must not be blank.')

    def __initDiscSubtitleTracks(self):
        """ For the disc subtitle track widgets:

                * Connect the buttons.
                * Create the widget/data connectors.
                * Create the validators.
        """

        # TODO enable/disable this button if title count > 0
        self.toolButton_Disc_Find_SubtitleTrack.clicked.connect(self.onDisc_Find_SubtitleTracks)

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


        # TODO Only one default, only one burned, a subtitle can't be both burned and default


        # Create the validators.
        # ======================================================================

        # TODO make sure all of the selected audio tracks exist in all of the selected titles.
        # TODO make sure at least on mixdown is selected

    def __initDiscTitleDetailWidgets(self):
        """ Initialze the tables used to display the detail information for a
            title.
        """
        # The table displaying the list of disc titles.
        # ======================================================================
        self.__StandardTableWidgetInitialization(self.tableWidget_Disc_Titles,
            ['Select', 'Title #', 'Duration', 'Aspect', 'Title Name'])

        self.tableWidget_Disc_Titles.itemSelectionChanged.connect(self.onDisc_Titles_ItemSelectionChanged)
        self.tableWidget_Disc_Titles.currentItemChanged.connect(self.onDisc_Titles_CurrentItemChanged)

        # The table displaying the detail information for the selected title.
        # ======================================================================
        idx = 0
        for label in ['vts:', 'ttn:', 'cells:', 'blocks:', 'duration:', 'size:',
            'pixel aspect:', 'display aspect:', 'fps:', 'autocrop:']:
            AddItemToTableWidgetCell(self.tableWidget_Disc_Title, idx, 0,
                label, textAlignment=None, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Title, idx, 1,
                '', readOnly=True)
            idx += 1

        self.__StandardTableWidgetInitialization(self.tableWidget_Disc_Title,
            ['Track', ''])

        # The table displaying the list of audio tracks for the selected disc title.
        # ======================================================================
        self.__StandardTableWidgetInitialization(self.tableWidget_Disc_Title_AudioTracks,
            [' # ', 'Audio Tracks'])

        # The table displaying the list of subtitle tracks for the selected title.
        # ======================================================================
        self.__StandardTableWidgetInitialization(self.tableWidget_Disc_Title_SubtitleTracks,
            [' # ', 'Subtitle Tracks'])

        # The table displaying the list of chapters for the selected title.
        # ======================================================================
        self.toolButton_Disc_Chapters_ResetFirstChapter.clicked.connect(self.onDisc_Chapters_ResetFirstChapter)
        self.pushButton_Disc_Chapters_ImportChapterNames.clicked.connect(self.onDisc_Chapters_ImportChapterNames)
        self.pushButton_Disc_Chapters_ResetNames.clicked.connect(self.onDisc_Chapters_ResetNames)
        self.pushButton_Disc_Chapters_ExportChapterNames.clicked.connect(self.onDisc_Chapters_ExportChapterNames)
        self.pushButton_Disc_Chapters_SetTitleEnd.clicked.connect(self.onDisc_Chapters_SetTitleEnd)

        self.radioButton_Disc_Chapters_NoMarkers.clicked.connect(self.onDisc_Title_EnbableChapterWidgets)
        self.radioButton_Disc_Chapters_IncludeMarkers.clicked.connect(self.onDisc_Title_EnbableChapterWidgets)
        self.radioButton_Disc_Chapters_IncludeNames.clicked.connect(self.onDisc_Title_EnbableChapterWidgets)

        self.__StandardTableWidgetInitialization(self.tableWidget_Disc_Chapters,
            ['Chapter #', 'Cells', 'Duration', 'Chapter Name'])

        self.radioButton_Disc_Chapters_IncludeMarkers.setChecked(True)      # Set this to enable/disable chapter controls
        self.onDisc_Title_EnbableChapterWidgets()

        # The widgets displaying the chapter ranges and episodes for the selected title.
        # ======================================================================
        self.toolButton_Disc_Title_ChapterRange_Reset.clicked.connect(self.onDisc_Title_ChapterRange_Reset)
        self.toolButton_Disc_Title_AddEpisode.clicked.connect(self.onDisc_Title_AddEpisode)
        self.toolButton_Disc_Title_CopyEpisode.clicked.connect(self.onDisc_Title_CopyEpisode)
        self.toolButton_Disc_Title_DeleteEpisode.clicked.connect(self.onDisc_Title_DeleteEpisode)
        self.toolButton_Disc_Title_Episodes_DeleteAll.clicked.connect(self.onButton_Disc_Title_Episodes_DeleteAll)

        self.radioButton_Disc_Title_AllChapters.clicked.connect(self.onDisc_Title_EnableChapterRangeWidgets)
        self.radioButton_Disc_Title_ChapterRange.clicked.connect(self.onDisc_Title_EnableChapterRangeWidgets)
        self.radioButton_Disc_Title_Episodes.clicked.connect(self.onDisc_Title_EnableChapterRangeWidgets)

        self.__StandardTableWidgetInitialization(self.tableWidget_Disc_Title_Episodes,
            ['First Chapter', 'Last Chapter', 'Title'])

        self.Disc_Title_Episodes_SpinBoxDelegate = SpinBoxDelegate()
        self.tableWidget_Disc_Title_Episodes.setItemDelegateForColumn(0, self.Disc_Title_Episodes_SpinBoxDelegate)
        self.tableWidget_Disc_Title_Episodes.setItemDelegateForColumn(1, self.Disc_Title_Episodes_SpinBoxDelegate)

        self.radioButton_Disc_Title_AllChapters.setChecked(True)      # Set this to enable/disable chapter controls
        self.onDisc_Title_EnableChapterRangeWidgets()

    @property
    def disc(self):
        """ Return the disc object."""
        return QApplication.instance().disc

    @property
    def preferences(self):
        """ Return the preferences object."""
        return QApplication.instance().preferences

    def activeTitle(self, warnIfNone=True):
        """ Returns the currently active title.

            The active title is attached to the first cell in the
            tableWidget_Disc_Title widget as UserRoll data.

            If warnIfNone is True (the default) a warning message will be
            displayed when a title does not exist.
        """
        title = self.tableWidget_Disc_Title.item(0, 0).data(Qt.UserRole)
        if (title is None and warnIfNone):
            QMessageBox.warning(self, 'Title Not Selected', 'Please select a title first.')

        return title

    def Load_Disc_FilenameTemplates(self):
        """ Load the filename templates QComboBox from the preferences.
        """

        text = self.comboBox_Disc_Mask.currentText()

        self.comboBox_Disc_Mask.clear()
        for filenameTemplate in self.preferences.filenameTemplates:
            self.comboBox_Disc_Mask.addItem(filenameTemplate)

        self.comboBox_Disc_Mask.setCurrentText(text)

    def Load_Disc_Presets(self):
        """ Load the presets QComboBox from the preferences.
        """

        text = self.comboBox_Disc_Preset.currentText()

        self.comboBox_Disc_Preset.clear()
        for preset in self.preferences.presets:
            self.comboBox_Disc_Preset.addItem(preset.name)

        self.comboBox_Disc_Preset.setCurrentText(text)

    def Load_Disc_MixdownTrackNumbers(self):
        """ Load the titles mixdown track ComboBoxes from the preferences.
        """

        # TODO use real track number from the Disc?  Must use highest available track number, can't change this per title because it applies to all titles.
        #       Probably not worth the effort.  If not, move this to __initDiscAudioTracks.

        self.comboBox_Disc_AudioTracks_SelectTrack_First.addItems(AudioTrackState.AUDIO_TRACK_CHOICES)
        self.comboBox_Disc_AudioTracks_SelectTrack_Second.addItems(AudioTrackState.AUDIO_TRACK_CHOICES)
        self.comboBox_Disc_AudioTracks_SelectTrack_Third.addItems(AudioTrackState.AUDIO_TRACK_CHOICES)

    def Load_Disc_Mixdowns(self):
        """ Load the titles mixdown ComboBoxes from the preferences.
        """

        # TODO enable/disable mixdown combo boxes -- if track is ''

        mixdowns = ['']
        for mixdown in self.preferences.mixdowns:
            mixdowns.append(mixdown.name)

        self.comboBox_Disc_AudioTracks_Mixdown_First_Primary.addItems(mixdowns)
        self.comboBox_Disc_AudioTracks_Mixdown_Second_Primary.addItems(mixdowns)
        self.comboBox_Disc_AudioTracks_Mixdown_Third_Primary.addItems(mixdowns)

        self.comboBox_Disc_AudioTracks_Mixdown_First_Secondary.addItems(mixdowns)
        self.comboBox_Disc_AudioTracks_Mixdown_Second_Secondary.addItems(mixdowns)
        self.comboBox_Disc_AudioTracks_Mixdown_Third_Secondary.addItems(mixdowns)

        self.comboBox_Disc_AudioTracks_Mixdown_Third_Secondary.update()

        self.groupBox_Disc_AudioTracks.updateGeometry()

    def Load_Disc_SubtitleTrackNumbers(self):
        """ Load the titles mixdown track ComboBoxes from the preferences.
        """

        self.comboBox_Disc_SubtitleTracks_SelectTrack_First.addItems(SubtitleTrackState.SUBTITLE_TRACK_CHOICES)
        self.comboBox_Disc_SubtitleTracks_SelectTrack_Second.addItems(SubtitleTrackState.SUBTITLE_TRACK_CHOICES)
        self.comboBox_Disc_SubtitleTracks_SelectTrack_Third.addItems(SubtitleTrackState.SUBTITLE_TRACK_CHOICES)

    def __NewEpisodeToTable(self, idx, episode):
        """ Insert a new episode in the tableWidget_Disc_Title_Episodes table.

            The talbe row (idx) must already exist.
        """
        AddItemToTableWidgetCell(self.tableWidget_Disc_Title_Episodes, idx, 0,
            episode.firstChapter, data=episode)
        AddItemToTableWidgetCell(self.tableWidget_Disc_Title_Episodes, idx, 1,
            episode.lastChapter)
        AddItemToTableWidgetCell(self.tableWidget_Disc_Title_Episodes, idx, 2,
            episode.title, textAlignment=None)

    def onDisc_Chapters_ExportChapterNames(self):
        """ Export the chapter names to a text file.
        """
        chapter = self.tableWidget_Disc_Chapters.item(0, 0).data(Qt.UserRole)
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
            for idx in range(self.tableWidget_Disc_Chapters.rowCount()):
                chapter = self.tableWidget_Disc_Chapters.item(idx, 0).data(Qt.UserRole)
                f.write("CHAPTER{:02d}NAME={}\n".format(chapter.chapterNumber, self.tableWidget_Disc_Chapters.item(idx, 3).text()))

        self.statusBar.showMessage('Chapter names exported to {}.'.format(result[0]), 15000)

    def onDisc_Chapters_ImportChapterNames(self):
        """ Import chapter names from a ChaptersDB.org text file.
        """
        result = QFileDialog.getOpenFileName(self, 'Open Chapter Names File',
            self.lineEdit_Disc_Source.text(), 'Text files (*.txt);;All files (*)')

        if (not result[0]):
            return

        idx = 0
        with open(result[0], "r") as f:
            for line in f:

                head, tail = line.rstrip("\r\n").split("=", 1)
                if (head.endswith("NAME")):
                    self.tableWidget_Disc_Chapters.item(idx, 3).setData(Qt.EditRole, tail)
                    idx += 1

        if (self.preferences.options.checkImportShortChapter):
            idx = self.tableWidget_Disc_Chapters.rowCount() - 1
            chapter = self.tableWidget_Disc_Chapters.item(idx, 0).data(Qt.UserRole)

            if (chapter.isShortChapter and chapter.isDefaultName):
                self.tableWidget_Disc_Chapters.item(idx, 3).setData(Qt.EditRole, self.preferences.options.textImportShortChapter)

        self.radioButton_Disc_Chapters_IncludeNames.setChecked(True)
        self.onDisc_Title_EnbableChapterWidgets()

        self.statusBar.showMessage('Chapter names imported from {}.'.format(result[0]), 15000)

    # TODO When enabling/disabling the All/Range/Episode radio buttons don't enable
    # the buttons if self.activeTitle() is None.

    def onDisc_Title_AddEpisode(self):
        """ Add a chapter episode.
        """
        title = self.activeTitle()
        if (title is None):
            return

        episode = title.chapterRanges.AddEpisode(title.chapters.lowestChapterNumber,
            title.chapters.highestChapterNumber, 'new episode')

        idx = self.tableWidget_Disc_Title_Episodes.rowCount()
        self.tableWidget_Disc_Title_Episodes.setRowCount(idx + 1)

        self.__NewEpisodeToTable(idx, episode)

        # If row count was zero enable the range copy/delete buttons.
        if (idx == 0):
            self.onDisc_Title_EnableChapterRangeWidgets()

        self.statusBar.showMessage('1 episode added.', 15000)

    def onDisc_Title_CopyEpisode(self):
        """ Copy a chapter episode.
        """
        title = self.activeTitle()
        if (title is None):
            return

        idx = self.tableWidget_Disc_Title_Episodes.currentRow()
        if (idx < 0):
            QMessageBox.warning(self, 'Episode Not Selected', 'Please select an episode first.')
            return

        episode = title.chapterRanges.AddEpisode(
            self.tableWidget_Disc_Title_Episodes.item(idx, 0).data(Qt.EditRole),
            self.tableWidget_Disc_Title_Episodes.item(idx, 1).data(Qt.EditRole),
            self.tableWidget_Disc_Title_Episodes.item(idx, 2).text()
        )

        idx = self.tableWidget_Disc_Title_Episodes.rowCount()
        self.tableWidget_Disc_Title_Episodes.setRowCount(idx + 1)

        self.__NewEpisodeToTable(idx, episode)

        self.statusBar.showMessage('1 episode copied.', 15000)

    def onDisc_Title_ChapterRange_Reset(self):
        """ Reset the chapter ranges for the selected title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        self.spinBox_Disc_Title_ChapterRange_First.setValue(title.chapters.lowestChapterNumber)
        self.spinBox_Disc_Title_ChapterRange_Last.setValue(title.chapters.highestChapterNumber)

        self.statusBar.showMessage('Chapter ranges reset.', 15000)

    def onDisc_Title_DeleteEpisode(self):
        """ Delete an episode from a titles.
        """
        title = self.activeTitle()
        if (title is None):
            return

        idx = self.tableWidget_Disc_Title_Episodes.currentRow()
        if (idx < 0):
            QMessageBox.warning(self, 'Episode Not Selected', 'Please select an episode first.')
            return

        episode = self.tableWidget_Disc_Title_Episodes.item(idx, 0).data(Qt.UserRole)
        title.chapterRanges.remove(episode)
        self.tableWidget_Disc_Title_Episodes.removeRow(idx)

        # If row count was zero enable the range copy/delete buttons.
        if (not self.tableWidget_Disc_Title_Episodes.rowCount()):
            self.onDisc_Title_EnableChapterRangeWidgets()

        self.statusBar.showMessage('1 episode deleted.', 15000)

    def onButton_Disc_Title_Episodes_DeleteAll(self):
        """ Delete all the episodes for the active title.
        """
        title = self.activeTitle()
        if (title is None):
            return

        rowCount = self.tableWidget_Disc_Title_Episodes.rowCount()

        result = QMessageBox.question(self, 'Delete All Episodes',
            'Are you sure you want to delete all {} episodes?'.format(rowCount))
        if (result != QMessageBox.Yes):
            return

        title.chapterRanges.clearEpisodes()
        self.tableWidget_Disc_Title_Episodes.setRowCount(0)
        self.onDisc_Title_EnableChapterRangeWidgets()

        self.statusBar.showMessage('{} episodes deleted.'.format(rowCount), 15000)

    def onDisc_Title_EnableChapterRangeWidgets(self, bool=False):
        """ Enable/disable the Set Title End button.  It's only enabled if
            the Include Names button is checked and the title has chapters.
        """
        rowCount = self.tableWidget_Disc_Chapters.rowCount()

        self.radioButton_Disc_Title_AllChapters.setEnabled(rowCount)
        self.radioButton_Disc_Title_ChapterRange.setEnabled(rowCount)
        self.radioButton_Disc_Title_Episodes.setEnabled(rowCount)

        # self.spinBox_Disc_Title_ChapterRange_First.setEnabled(rowCount)
        # self.spinBox_Disc_Title_ChapterRange_First.setEnabled(rowCount)
        # self.toolButton_Disc_Chapters_ResetFirstChapter.setEnabled(rowCount)

        self.spinBox_Disc_Title_ChapterRange_First.setEnabled(self.radioButton_Disc_Title_ChapterRange.isChecked())
        self.spinBox_Disc_Title_ChapterRange_Last.setEnabled(self.radioButton_Disc_Title_ChapterRange.isChecked())
        self.toolButton_Disc_Title_ChapterRange_Reset.setEnabled(self.radioButton_Disc_Title_ChapterRange.isChecked())

        self.tableWidget_Disc_Title_Episodes.setEnabled(self.radioButton_Disc_Title_Episodes.isChecked())
        self.toolButton_Disc_Title_AddEpisode.setEnabled(self.radioButton_Disc_Title_Episodes.isChecked())
        self.toolButton_Disc_Title_CopyEpisode.setEnabled(self.radioButton_Disc_Title_Episodes.isChecked()
            and self.tableWidget_Disc_Title_Episodes.rowCount() > 0)
        self.toolButton_Disc_Title_DeleteEpisode.setEnabled(self.radioButton_Disc_Title_Episodes.isChecked()
            and self.tableWidget_Disc_Title_Episodes.rowCount() > 0)
        self.toolButton_Disc_Title_Episodes_DeleteAll.setEnabled(self.radioButton_Disc_Title_Episodes.isChecked()
            and self.tableWidget_Disc_Title_Episodes.rowCount() > 0)

        if (self.radioButton_Disc_Title_AllChapters.isChecked()):
            self.tabWidget_Disc.setTabIcon(2, QIcon())
        else:
            self.tabWidget_Disc.setTabIcon(2, self.highlightedTabIcon)

    def onDisc_Title_EnbableChapterWidgets(self, bool=False):
        """ Enable/disable the widgets associated with chapter editing.
        """
        rowCount = self.tableWidget_Disc_Chapters.rowCount()

        self.radioButton_Disc_Chapters_NoMarkers.setEnabled(rowCount)
        self.radioButton_Disc_Chapters_IncludeMarkers.setEnabled(rowCount)
        self.radioButton_Disc_Chapters_IncludeNames.setEnabled(rowCount)

        self.spinBox_Disc_Chapters_FirstChapter.setEnabled(rowCount)
        self.toolButton_Disc_Chapters_ResetFirstChapter.setEnabled(rowCount)

        enableWidgets = (rowCount
            and self.radioButton_Disc_Chapters_IncludeNames.isChecked())

        self.pushButton_Disc_Chapters_ImportChapterNames.setEnabled(self.tableWidget_Disc_Chapters.rowCount())

        self.pushButton_Disc_Chapters_ExportChapterNames.setEnabled(enableWidgets)
        self.pushButton_Disc_Chapters_ResetNames.setEnabled(enableWidgets)
        self.pushButton_Disc_Chapters_SetTitleEnd.setEnabled(enableWidgets)

        self.tableWidget_Disc_Chapters.setEnabled(enableWidgets)

        if (self.radioButton_Disc_Chapters_IncludeMarkers.isChecked()):
            self.tabWidget_Disc.setTabIcon(1, QIcon())
        else:
            self.tabWidget_Disc.setTabIcon(1, self.highlightedTabIcon)

    # TODO add status bar messages for lots of actions

    def onDisc_Chapters_ResetFirstChapter(self):
        """ Reset the first chapter number.
        """
        self.spinBox_Disc_Chapters_FirstChapter.setValue(1)

        self.statusBar.showMessage('First chapter number reset to 1.', 15000)

    # TODO refactor method names, especially buttons | onDisc_Chapters_ResetNames becomes onButton_Disc_Chapters_ResetNames
    # TODO onSignal, etc.

    def onDisc_Chapters_ResetNames(self):
        """ Reset the chapter names to their default values.
        """
        for idx in range(self.tableWidget_Disc_Chapters.rowCount()):
            chapter = self.tableWidget_Disc_Chapters.item(idx, 0).data(Qt.UserRole)
            self.tableWidget_Disc_Chapters.item(idx, 3).setData(Qt.EditRole, chapter.defaultName)

        self.statusBar.showMessage('Chapter names reset.', 15000)

    def onDisc_Chapters_SetTitleEnd(self):
        """ Set the last chapter name to the preferences short title if it is a
            short title.
        """
        idx = self.tableWidget_Disc_Chapters.rowCount() - 1
        chapter = self.tableWidget_Disc_Chapters.item(idx, 0).data(Qt.UserRole)

        if (not chapter.isShortChapter):
            result = QMessageBox.question(self, 'Set Short Chapter',
                'Chapter () is not a short chapter.  Do you want to continue?'.format(chapter.chapterNumber))
            if (result != QMessageBox.Yes):
                return

        if (self.tableWidget_Disc_Chapters.item(idx, 3).text() != chapter.defaultName):
            result = QMessageBox.question(self, 'Set Short Chapter',
                'The name for chapter {} is not the default name.  Do you want to continue?'.format(chapter.chapterNumber))
            if (result != QMessageBox.Yes):
                return

        self.tableWidget_Disc_Chapters.item(idx, 3).setData(Qt.EditRole, self.preferences.options.textImportShortChapter)

        self.statusBar.showMessage('The name for chapter {} was set to {}.'.format(chapter.chapterNumber,
            self.preferences.options.textImportShortChapter), 15000)

    def onDisc_Destination_Browse(self):
        """ Select a folder where the transcoded video files will be saved.
        """
        destinationFolder = QFileDialog.getExistingDirectory(self,
            'Select Destination Folder', self.lineEdit_Disc_Destination.text())
        if (not destinationFolder):
            return

        self.lineEdit_Disc_Destination.setText(destinationFolder)
        self.Validator_Disc_Destination.clearHighlight()

    def onDisc_Find_AudioTracks(self):
        """ Find the audio track and mixdown settings for the first visible,
            selected title.  Then set the disc audio track states and update the
            widgets.

            Use the default title is nothing matches.
        """
        matchingTitles = self.disc.titles.GetMatchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        if (len(matchingTitles.matchingTitles)):
            matchingTitle = matchingTitles.matchingTitles[0]
        else:
            matchingTitle = matchingTitles.defaultTitle

        self.disc.audioTrackStates.AutoSet_From_AudioTracks(
            matchingTitle.audioTracks,
            self.preferences)

        self.TransferToWindow(self.WIDGET_GROUP_DISC_AUTO_AUDIO)
        self.statusBar.showMessage('Audio track selections updated.', 15000)

    def onDisc_Find_Crop(self):
        """ Find the cropping values for the first selected title. Then set the
            disc cropping values and update the widgets.

            Use the default title is nothing matches.
        """
        matchingTitles = self.disc.titles.GetMatchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        if (len(matchingTitles.matchingTitles)):
            matchingTitle = matchingTitles.matchingTitles[0]
        else:
            matchingTitle = matchingTitles.defaultTitle

        self.disc.customCrop.Copy(matchingTitle.autoCrop)
        self.disc.customCrop.processChoice = self.disc.customCrop.PROCESS_AUTOMATIC

        self.TransferToWindow(self.WIDGET_GROUP_DISC_CROP)
        self.statusBar.showMessage('Cropping selections updated.', 15000)

    def onDisc_Find_SubtitleTracks(self):
        """ Find the Subtitle track for the first selected title. Then set the
            disc subtitle track states and update the widgets.

            Use the default title is nothing matches.
        """
        matchingTitles = self.disc.titles.GetMatchingTitles(Titles.FLAG_SELECTED
            | Titles.FLAG_VISIBLE)

        if (len(matchingTitles.matchingTitles)):
            matchingTitle = matchingTitles.matchingTitles[0]
        else:
            matchingTitle = matchingTitles.defaultTitle

        self.disc.subtitleTrackStates.AutoSet_From_SubtitleTracks(
            matchingTitle.subtitleTracks,
            self.preferences)

        self.TransferToWindow(self.WIDGET_GROUP_DISC_AUTO_SUBTITLE)
        self.statusBar.showMessage('Subtitle track selections updated.', 15000)


        # TODO subtitle tracks validators - if burn, focus or default checked then corresponding combobox must have a track selected.

    def onDisc_Reset_EpisodeNumberPrecision(self):
        """ Reset the first episode number precision to it's default value.
        """
        self.spinBox_Disc_EpisodeNumberPrecision.setValue(self.disc.DEFAULT_EPISODE_NUMBER_PRECISION)

    def onDisc_Reset_FirstEpisode(self):
        """ Reset the first episode number to it's default value.
        """
        self.spinBox_Disc_FirstEpisode.setValue(self.disc.DEFAULT_FIRST_EPISODE_NUMBER)

    def onDisc_Source_Browse(self):
        """ Find a video folder with containing a copy of a DVD or BluRay disc
            and read the disc with Handbrake.  Then parse the disc information.
        """
        sourceFolder = QFileDialog.getExistingDirectory(self,
            'Select Video Folder', self.lineEdit_Disc_Source.text())
        if (not sourceFolder):
            return

        self.lineEdit_Disc_Source.setText(sourceFolder)
        self.lineEdit_Disc_Source.setStyleSheet('')
        self.disc.source = sourceFolder

        if (not self.__ReadSource()):
            return

        self.__onNewSource()

        self.TransferToWindow()

    def onDisc_Source_Find(self):
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

    def onDisc_Source_Read(self):
        """ Re-read the disc with Handbrake.  Then parse the disc information.
        """

        if (not self.Validator_Disc_Source.isValid()):
            return

        if (not self.__ReadSource()):
            return

        # TODO default destination was not set.

        self.TransferToWindow()

    # def onDisc_Title_AllChapters(self, enabled):
    #     """ Enable/disable the chapter range controls in response to the all
    #         chapters radio button.
    #     """





    def onDisc_Titles_CurrentItemChanged(self, currentItem, previousItem):
        """ Triggered when a new title is selected.
        """

        print (currentItem, previousItem)
        if (currentItem):
            print ('current', currentItem.row())
        if (previousItem):
            print ('previous', previousItem.row())

    def onDisc_Titles_ItemSelectionChanged(self):
        """ Triggered when a new title is selected.
        """
        self.__TitleDetailsFromWidgets()

        currentItem = self.tableWidget_Disc_Titles.currentItem()
        if (currentItem is None):       # This will be None if we're here because the selected row was deleted.
            return

        title = self.tableWidget_Disc_Titles.item(currentItem.row(), 0).data(Qt.UserRole)
        self.__TitleDetailsToWidgets(title)

    def __StandardTableWidgetInitialization(self, tableWidget, horizontalHeaderLabels=None):
        """ Standard initialization for a QTableWidget.
        """
        if (horizontalHeaderLabels is not None):
            tableWidget.setHorizontalHeaderLabels(horizontalHeaderLabels)
            tableWidget.resizeColumnsToContents()
            tableWidget.horizontalHeader().setStretchLastSection(True)

        tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        tableWidget.verticalHeader().setDefaultSectionSize(21)

    def __TitleDetailsToWidgets(self, title):
        """ Update the title detail widgets from the title.
        """
        # Update the title details table.
        # ======================================================================
        self.tableWidget_Disc_Title.item(0, 0).setData(Qt.UserRole, title)

        self.tableWidget_Disc_Title.item(0, 1).setData(Qt.EditRole, title.vts)
        self.tableWidget_Disc_Title.item(1, 1).setData(Qt.EditRole, title.ttn)
        self.tableWidget_Disc_Title.item(2, 1).setData(Qt.EditRole, title.cellsRange)
        self.tableWidget_Disc_Title.item(3, 1).setData(Qt.EditRole, title.blocks)
        self.tableWidget_Disc_Title.item(4, 1).setData(Qt.EditRole, title.duration)
        self.tableWidget_Disc_Title.item(5, 1).setData(Qt.EditRole, title.sizeRange)
        self.tableWidget_Disc_Title.item(6, 1).setData(Qt.EditRole, title.pixelAspectRatio)
        self.tableWidget_Disc_Title.item(7, 1).setData(Qt.EditRole, title.displayAspectRatio)
        self.tableWidget_Disc_Title.item(8, 1).setData(Qt.EditRole, title.framesPerSecond)
        self.tableWidget_Disc_Title.item(9, 1).setData(Qt.EditRole, title.autoCrop.asString)

        # Update the title audio tracks table.
        # ======================================================================
        self.tableWidget_Disc_Title_AudioTracks.setRowCount(len(title.audioTracks))

        idx = 0
        for audioTrack in title.audioTracks:
            AddItemToTableWidgetCell(self.tableWidget_Disc_Title_AudioTracks,
                idx, 0, audioTrack.trackNumber, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Title_AudioTracks,
                idx, 1, audioTrack.description, textAlignment=None, readOnly=True)

            idx += 1

        self.tableWidget_Disc_Title_AudioTracks.resizeColumnToContents(0)

        # Update the subtitle tracks table.
        # ======================================================================
        self.tableWidget_Disc_Title_SubtitleTracks.setRowCount(len(title.subtitleTracks))

        idx = 0
        for subtitleTrack in title.subtitleTracks:
            AddItemToTableWidgetCell(self.tableWidget_Disc_Title_SubtitleTracks,
                idx, 0, subtitleTrack.trackNumber, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Title_SubtitleTracks,
                idx, 1, subtitleTrack.description, textAlignment=None, readOnly=True)

            idx += 1

        self.tableWidget_Disc_Title_SubtitleTracks.resizeColumnToContents(0)

        # Update the chapters widgets.
        # ======================================================================
        if (title.chapters.processChoice == title.chapters.PROCESS_MARKERS):
            self.radioButton_Disc_Chapters_IncludeMarkers.setChecked(True)
        elif (title.chapters.processChoice == title.chapters.PROCESS_NAMES):
            self.radioButton_Disc_Chapters_IncludeNames.setChecked(True)
        else:
            self.radioButton_Disc_Chapters_NoMarkers.setChecked(True)

        self.spinBox_Disc_Chapters_FirstChapter.setValue(title.chapters.firstChapterNumber)

        self.tableWidget_Disc_Chapters.setRowCount(len(title.chapters))
        idx = 0
        for chapter in title.chapters:
            AddItemToTableWidgetCell(self.tableWidget_Disc_Chapters, idx, 0,
                chapter.chapterNumber, data=chapter, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Chapters, idx, 1,
                chapter.cellsString, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Chapters, idx, 2,
                chapter.duration, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Chapters, idx, 3,
                chapter.title, textAlignment=None)

            idx += 1

        self.tableWidget_Disc_Chapters.resizeColumnsToContents()

        self.onDisc_Title_EnbableChapterWidgets()

        # Update the chapter ranges widgets.
        # ======================================================================
        if (title.chapterRanges.processChoice == title.chapterRanges.PROCESS_RANGE):
            self.radioButton_Disc_Title_ChapterRange.setChecked(True)
        elif (title.chapterRanges.processChoice == title.chapterRanges.PROCESS_EPISODES):
            self.radioButton_Disc_Title_Episodes.setChecked(True)
        else:
            self.radioButton_Disc_Title_AllChapters.setChecked(True)       # PROCESS_ALL

        self.spinBox_Disc_Title_ChapterRange_First.setMinimum(title.chapters.lowestChapterNumber)
        self.spinBox_Disc_Title_ChapterRange_Last.setMinimum(title.chapters.lowestChapterNumber)

        self.spinBox_Disc_Title_ChapterRange_First.setMaximum(title.chapters.highestChapterNumber)
        self.spinBox_Disc_Title_ChapterRange_Last.setMaximum(title.chapters.highestChapterNumber)

        if (title.chapterRanges.firstChapter == 0):
            self.spinBox_Disc_Title_ChapterRange_First.setValue(title.chapters.lowestChapterNumber)
        else:
            self.spinBox_Disc_Title_ChapterRange_First.setValue(title.chapterRanges.firstChapter)

        if (title.chapterRanges.lastChapter == 0):
            self.spinBox_Disc_Title_ChapterRange_Last.setValue(title.chapters.highestChapterNumber)
        else:
            self.spinBox_Disc_Title_ChapterRange_Last.setValue(title.chapterRanges.lastChapter)

        # if (not len(title.chapterRanges.episodes)):
        #     title.chapterRanges.AddEpisode(1, 2, 'First')
        #     title.chapterRanges.AddEpisode(3, 4, 'Second')
        #     title.chapterRanges.AddEpisode(5, 6, 'Third')

        # This works because Python passes class objects by reference.  So, the
        # delegate for the first and second columns and this attribute are all
        # the same object.  Remember, a new spinbox is created every time a cell
        # is edited.
        self.Disc_Title_Episodes_SpinBoxDelegate.minimum = title.chapters.lowestChapterNumber
        self.Disc_Title_Episodes_SpinBoxDelegate.maximum = title.chapters.highestChapterNumber

        self.tableWidget_Disc_Title_Episodes.setRowCount(len(title.chapterRanges.episodes))
        idx = 0
        for episode in title.chapterRanges.episodes:
            self.__NewEpisodeToTable(idx, episode)
            idx += 1

        # self.tableWidget_Disc_Title_Episodes.resizeColumnsToContents()

        self.onDisc_Title_EnableChapterRangeWidgets()

    def __TitleDetailsFromWidgets(self):
        """ Update the title details from the title detail widgets.

            Only the editable items are updated.
        """
        title = self.activeTitle(False)
        if (title is None):
            return

        # Update the title chapters table.
        # ======================================================================
        if self.radioButton_Disc_Chapters_IncludeMarkers.isChecked():
            title.chapters.processChoice = title.chapters.PROCESS_MARKERS
        if self.radioButton_Disc_Chapters_IncludeNames.isChecked():
            title.chapters.processChoice = title.chapters.PROCESS_NAMES
        if self.radioButton_Disc_Chapters_NoMarkers.isChecked():
            title.chapters.processChoice = title.chapters.PROCESS_NONE

        title.chapters.firstChapterNumber = self.spinBox_Disc_Chapters_FirstChapter.value()

        for idx in range(self.tableWidget_Disc_Chapters.rowCount()):
            chapter = self.tableWidget_Disc_Chapters.item(idx, 0).data(Qt.UserRole)
            chapter.title = self.tableWidget_Disc_Chapters.item(idx, 3).data(Qt.EditRole)

        # Update the chapter ranges widgets.
        # ======================================================================
        if (self.radioButton_Disc_Title_AllChapters.isChecked()):
            title.chapterRanges.processChoice = title.chapterRanges.PROCESS_ALL
        if (self.radioButton_Disc_Title_ChapterRange.isChecked()):
            title.chapterRanges.processChoice = title.chapterRanges.PROCESS_RANGE
        if (self.radioButton_Disc_Title_Episodes.isChecked()):
            title.chapterRanges.processChoice = title.chapterRanges.PROCESS_EPISODES

        title.chapterRanges.firstChapter = self.spinBox_Disc_Title_ChapterRange_First.value()
        title.chapterRanges.lastChapter = self.spinBox_Disc_Title_ChapterRange_Last.value()

        title.chapterRanges.clearEpisodes()
        for idx in range(self.tableWidget_Disc_Title_Episodes.rowCount()):
            title.chapterRanges.AddEpisode(
                self.tableWidget_Disc_Title_Episodes.item(idx, 0).data(Qt.EditRole),
                self.tableWidget_Disc_Title_Episodes.item(idx, 1).data(Qt.EditRole),
                self.tableWidget_Disc_Title_Episodes.item(idx, 2).data(Qt.EditRole)
            )

    def onEditPreferences(self):
        """Edit the application preferences."""

        dlg = PreferencesDialog(self.preferences, self)
        dlg.TransferToWindow()
        result = dlg.exec_()
        if (result):
            dlg.TransferFromWindow()
            QApplication.instance().SavePreferences()
            QApplication.instance().preferences.logging.InitLog()

            self.Load_Disc_FilenameTemplates()
            self.Load_Disc_Presets()
            self.Load_Disc_Mixdowns()

            DiscFilenameTemplatesSingleton().Set(self.preferences.filenameTemplates)
            DiscPresetsSingleton().Set(self.preferences.presets.GetNames())
            TitleVisibleSingleton().minimumTitleSeconds = self.preferences.autoTitle.minimumTitleSeconds

            log = SingletonLog()
            log.writeline('Preferences updated')

    def onEditSourceDiskLabel(self):
        """ Get the disk label from the user.
        """

        text, ok  = QInputDialog.getText(self, 'Set Disk Volume Label', 'Volume label',
            text = self.lineEdit_Disc_DiskLabel.text())

        if (ok):
            self.lineEdit_Disc_DiskLabel.setText(text)
            self.Validator_Disc_DiskLabel.clearHighlight()

    def onGetSourceDiskLabel(self):
        """ Get the volume label for the disk where the source is located.

            Only Windows disks have volume labels.
        """

        if (sys.platform == 'win32'):
            volumeLabel = GetVolumeLabel(lineEdit_Disc_Source.text())
            self.lineEdit_Disc_DiskLabel.setText(volumeLabel)

    def __onNewSource(self):
        """ Stuff to do after a new source is parsed.
        """

        # Disc stuff
        # ======================================================================
        self.onGetSourceDiskLabel()

        if (not self.lineEdit_Disc_Destination.text()):
            if (self.preferences.newSource.useDefaultDestination):
                self.lineEdit_Disc_Destination.setText(self.preferences.newSource.defaultDestination)
                self.disc.destination = self.preferences.newSource.defaultDestination

        # File Name
        # ======================================================================
        if (self.preferences.newSource.firstMask):
            self.comboBox_Disc_Mask.setCurrentIndex(0)

        # Processing
        # ======================================================================
        if (self.preferences.newSource.firstPreset):
            self.comboBox_Disc_Preset.setCurrentIndex(0)

        # First Selected Title or Longest Title
        # ======================================================================
        matchingTitles = self.disc.titles.GetMatchingTitles()

        if (self.preferences.autoTitle.autoSelectLongestTitle):
            matchingTitles.longestTitle.selected = True

        self.disc.audioTrackStates.AutoSet_From_AudioTracks(
            matchingTitles.longestTitle.audioTracks,
            self.preferences)

        self.disc.subtitleTrackStates.AutoSet_From_SubtitleTracks(
            matchingTitles.longestTitle.subtitleTracks,
            self.preferences)



        # TODO Automatically hide short titles if more than nnn are found.   AnalyzeTitles() function?


        if (self.preferences.autoCrop.autoCopyCrop):
            self.disc.customCrop.Copy(matchingTitles.longestTitle.autoCrop)




    def onSaveHashSession(self):
        """ Create an xml file using the disc hash.  The file will contain the disc
            information and the disc state data.
        """

        # wx.GetApp().SaveSession()
        # wx.GetApp().SetAutoSessionFilename()
        # wx.GetApp().SaveSession()
        # self.NewSessionFile()
        #
        # self.ShowMessage("Hash session saved.")

        self.__SaveSession(QApplication.instance().hashSessionFilename)

    # TODO create class for cells and size information (separate classes)
    # TODO base cells, size, crop classes on list, set?

    def onVLC(self):
        """ Start VLC using the source path.
        """

        if (not self.Validator_Disc_Source.isValid()):
            return

        # process = QProcess(QApplication.instance())
        started = QProcess.startDetached('"{}" "{}"'.format(self.preferences.executables.VLC, self.lineEdit_Disc_Source.text()))

        if (not started):
            QMessageBox.critical(self, 'Run Error',
                'An error has occurred while running VLC.\nVLC did not start.')
            return False

    def __ReadSource(self):
        """ Read the disc with Handbrake from the source with HandBrake, then
            parse the disc information.

            Returns True if the source was successfully read.
        """
        with QWaitCursor():
            parameters = ['-t', '0', ]

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

            if (process.exitCode() != 0):
                QMessageBox.critical(self, 'Run Error',
                    'An error has occurred while running HandBrake.\nExit code = {}\n{}'.format(process.exitCode(),
                    bytearray(process.readAllStandardError()).decode('utf-8')))
                return False

            # Don't know why but HandBrake returns the results on StandardError not StandardOutput (linux)
            self.disc.Parse(bytearray(process.readAllStandardError()).decode('utf-8'))

            self.statusBar.showMessage('Source folder "{}" was read.'.format(self.lineEdit_Disc_Source.text()), 15000)
            return True

    def __SaveSession(self, sessionFilename):
        """ Save the disc information and the disc state data to an xml file.
        """
        if (not self.Validate()):
            QMessageBox.critical(self, 'Validation Errors',
                'One or more errors were found.\nPlease correct the errors and try again.\nSession was not saved.')
            return False






        self.TransferFromWindow()

        dom = minidom.getDOMImplementation()
        doc = dom.createDocument(None, "HEP", None)
        parentElement = doc.documentElement

        # self.frame.SaveState(doc, parentElement)
        QApplication.instance().disc.ToXML(doc, parentElement)
        # self.titles.ToXML(doc, parentElement)







        if (__TESTING_DO_NOT_SAVE_SESSION__):
            self.statusBar.showMessage('TESTING!!! Session was not saved to "{}".'.format(sessionFilename), 15000)
        else:
            xmlFile = open(sessionFilename, "w")
            doc.writexml(xmlFile, "", "\t", "\n")
            xmlFile.close()

            self.statusBar.showMessage('Session saved to "{}".'.format(sessionFilename), 15000)







        doc.unlink()

        # self.SaveFileHistory()

    def TransferFromWindow(self, groupFlags=0):
        """ Copy the data from the preferences object to the dialog widgets.
        """

        self.__widgetDataConnectors.transferFromWidgets(groupFlags)

    def __TransferToDiscTables(self):
        """ Copy the data from the preferences object to the dialog widgets.
        """

        # Transfer the disc titles to the disc titles table.
        # ======================================================================
        self.tableWidget_Disc_Titles.setRowCount(0)     # remove all existing rows
        self.tableWidget_Disc_Titles.setRowCount(len(self.disc.titles))     # add a row for each title

        # TODO transfer by order number
        titleKeys = sorted(self.disc.titles.titlesByOrderNumber.keys())
        idx = 0
        for key in titleKeys:
            title = self.disc.titles.titlesByOrderNumber[key]

            item = QTableWidgetItem()
            # item.setCheckState(BoolToQtChecked(title.selected))

            widget = QWidget()
            checkBox = QCheckBox()
            checkBox.setCheckState(BoolToQtChecked(title.selected))
            layout = QHBoxLayout(widget)
            layout.addWidget(checkBox, alignment=Qt.AlignCenter)
            layout.setContentsMargins(0,0,0,0);
            widget.setLayout(layout)
            self.tableWidget_Disc_Titles.setCellWidget(idx, 0, widget)

            # Add an item behind the checkbox.  It's need to generate item change signals.
            AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, idx, 0,
                None, data=title, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, idx, 1,
                title.titleNumber, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, idx, 2,
                title.duration, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, idx, 3,
                title.displayAspectRatio, readOnly=True)
            AddItemToTableWidgetCell(self.tableWidget_Disc_Titles, idx, 4,
                title.title, textAlignment=None)

            self.tableWidget_Disc_Titles.setRowHidden(idx, not title.visible)

            idx += 1

        for idx in range(self.tableWidget_Disc_Titles.rowCount()):
            if (not self.tableWidget_Disc_Titles.isRowHidden(idx)):
                self.tableWidget_Disc_Titles.setCurrentCell(idx, 1)
                break

    def TransferToWindow(self, groupFlags=0):
        """ Copy the data from the preferences object to the dialog widgets.
        """

        self.__widgetDataConnectors.transferToWidgets(groupFlags)

        self.__TransferToDiscTables()

    def Validate(self):
        """ Validate the fields on the main window.
        """

        notValid = False

        notValid |= (not self.Validator_Disc_Source.isValid())
        notValid |= (not self.Validator_Disc_Destination.isValid())
        notValid |= (not self.Validator_Disc_DiskLabel.isValid())
        notValid |= (not self.Validator_Disc_Title.isValid())
        notValid |= (not self.Validator_Disc_Mask.isValid())

        return (not notValid)

    # def Validate_Disc_Source(self):
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
