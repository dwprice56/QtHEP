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

from collections import MutableSequence

from SubtitleTrackStates import (SubtitleTrackState, SubtitleTrackStates)

# TODO button to open log file

class SubtitleTrackWidgets(object):
    """ Contains the widgets for a single subtitle track.
    """

    def __init__(self, parent, index, trackWidget, forcedWidget, burnWidget,
        defaultWidget):

        self.__parent = parent
        self.index = index              # It's always nice to know where you are.

        self.trackWidget = trackWidget
        self.forcedWidget = forcedWidget
        self.burnWidget = burnWidget
        self.defaultWidget = defaultWidget

        self.trackWidget.currentTextChanged.connect(self.onSignal_trackWidget_currentTextChanged)
        self.burnWidget.clicked.connect(self.onCheckBox_stateChanged_Burn)
        self.defaultWidget.clicked.connect(self.onCheckBox_stateChanged_Default)

    # def __str__(self):
    #     return '{}: id={}, index={}, track={}, forced={}, burn={}'\
    #         .format(self.XMLNAME, id(self),
    #         self.index, self.track, self.forced, self.burn)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.trackWidget.setCurrentText('')
        self.forcedWidget.setChecked(False)
        self.burnWidget.setChecked(False)
        self.defaultWidget.setChecked(False)

    @property
    def parent(self):
        return self.__parent

    def addTrackItems(self, items):
        """ Add the dropdown list items to the track widget.
        """
        self.trackWidget.clear()
        self.trackWidget.addItems(items)

    def onSignal_trackWidget_currentTextChanged(self, text=None):
        """ Enable/disable the mixdown widgets, based on the track widget.
        """
        enableCheckBoxes = (self.trackWidget.currentText() != '')

        self.forcedWidget.setEnabled(enableCheckBoxes)
        self.burnWidget.setEnabled(enableCheckBoxes)
        self.defaultWidget.setEnabled(enableCheckBoxes)

    def setEnabled(self, enabled):
        """ Enable/disable all of the subtitle track widgets.
        """
        self.trackWidget.setEnabled(enabled)
        self.forcedWidget.setEnabled(enabled)
        self.burnWidget.setEnabled(enabled)
        self.defaultWidget.setEnabled(enabled)

    def setTrackStateFromWidgets(self, trackState):
        """ Sets the trackState attributes from the subtitle track widgets.
        """
        assert(isinstance(trackState, SubtitleTrackState))

        trackState.track = self.trackWidget.currentText()
        trackState.forced = self.forcedWidget.isChecked()
        trackState.burn = self.burnWidget.isChecked()
        trackState.default = self.defaultWidget.isChecked()

    def setWidgetsFromTrackState(self, trackState):
        """ Set the currentText()/selection for the subtitle track widgets from
            the subtitle track state.
        """
        assert(isinstance(trackState, SubtitleTrackState))

        self.trackWidget.setCurrentText(trackState.track)
        self.forcedWidget.setChecked(trackState.forced)
        self.burnWidget.setChecked(trackState.burn)
        self.defaultWidget.setChecked(trackState.default)

    def onCheckBox_stateChanged_Burn(self, state):
        """ The burn checkbox was checked/unchecked.

            The 'state' variable is True/False unless this is a tri-state checkbox.

            Only one subtitle can be burned and burn & default are mutually
            exclusive.  Propigate this signal to the list to check this.
        """
        if (state):
            if (self.defaultWidget.isChecked()):
                self.defaultWidget.setChecked(False)

            self.parent.CheckBox_stateChanged(state, self.index)

    def onCheckBox_stateChanged_Default(self, state):
        """ The default checkbox was checked/unchecked.

            The 'state' variable is True/False unless this is a tri-state checkbox.

            Only one subtitle can be the default and burn & default are mutually
            exclusive.  Propigate this signal to the list to check this.
        """
        if (state):
            if (self.burnWidget.isChecked()):
                self.burnWidget.setChecked(False)

            self.parent.CheckBox_stateChanged(state, self.index)

class SubtitleTrackWidgetsList(MutableSequence):
    """ Container for a list of SubtitleTrackWidgets.
    """

    def __init__(self, parent):
        self.__parent = parent

        self.trackWidgetsList = []

    # def __str__(self):
    #     return '{}: id={}, len={}, processChoice="{}"'.format(self.XMLNAME, id(self),
    #     len(self.trackWidgetsList), self.processChoice)

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.trackWidgetsList[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, SubtitleTrackWidgets))
        self.trackWidgetsList[idx] = obj

    def __delitem__(self, idx):
        del self.trackWidgetsList[idx]

    def __len__(self):
        return len(self.trackWidgetsList)

    def insert(self, idx, obj):
        assert(isinstance(obj, SubtitleTrackWidgets))
        self.trackWidgetsList.insert(idx, obj)
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """
        for trackWidgets in self.trackWidgetsList:
            trackWidgets.clear()

    @property
    def parent(self):
        return self.__parent

    def addTrackItems(self, items):
        """ Add the track items to all track widgets.
        """
        for trackWidgets in self.trackWidgetsList:
            trackWidgets.addTrackItems(items)

    def addMixdownItems(self, items):
        """ Add the mixdown items to all mixdown widgets.
        """
        for trackWidgets in self.trackWidgetsList:
            trackWidgets.addMixdownItems(items)

    def enableCheckBoxes(self):
        """ Enable/disable the checkboxes for all entries in the list
        """
        for trackWidgets in self.trackWidgetsList:
            trackWidgets.onSignal_trackWidget_currentTextChanged()

    def setEnabled(self, enabled):
        """ Enable/disable all of the subtitle track widgets.
        """
        for trackWidgets in self.trackWidgetsList:
            trackWidgets.setEnabled(enabled)

    # TODO rename subtitleTrackStates to trackStates; do the same for audioTrackStates
    # TODO add instance assert; subtitleTrackStates is SubtitleTrackStates; same for audioTrackStates

    def setTrackStatesFromWidgets(self, trackStates):
        """ Set the list of subtitle track states from list of widgets.
        """
        assert(isinstance(trackStates, SubtitleTrackStates))
        assert(len(trackStates) == len(self.trackWidgetsList))

        for idx in range(len(trackStates)):
            self.trackWidgetsList[idx].setTrackStateFromWidgets(trackStates[idx])

    def setWidgetsFromTrackStates(self, trackStates):
        """ Set the currentText()/selection for the subtitle track widgets from
            a list of subtitle track states.
        """
        assert(isinstance(trackStates, SubtitleTrackStates))
        assert(len(trackStates) == len(self.trackWidgetsList))

        for idx in range(len(trackStates)):
            self.trackWidgetsList[idx].setWidgetsFromTrackState(trackStates[idx])

    def CheckBox_stateChanged(self, state, index):
        """ A burn or default checkbox was checked/unchecked.

            The 'state' variable is True/False unless this is a tri-state checkbox.

            Only one subtitle can be burned and burn & default are mutually
            exclusive.  Check the subtitle widgets for this case.
        """
        if (state):       # Theoretically, this method is only called if this is True but...
            for trackWidgets in self.trackWidgetsList:
                if (trackWidgets.index == index):       # Skip the item that called this method.
                    continue

                if (trackWidgets.burnWidget.isChecked()):
                    trackWidgets.burnWidget.setChecked(False)

                if (trackWidgets.defaultWidget.isChecked()):
                    trackWidgets.defaultWidget.setChecked(False)
