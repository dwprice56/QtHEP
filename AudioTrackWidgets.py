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

from PyQt5.QtWidgets import QApplication

from AudioTrackStates import (AudioTrackState, AudioTrackStates)
from PyQt5Helpers import UpdateComboBox

class AudioTrackWidgets(object):
    """ Contains the widgets for a single audio track.
    """

    def __init__(self, parent, index, trackWidget, primaryMixdownWidget,
        secondaryMixdownWidget):

        self.__parent = parent
        self.index = index              # It's always nice to know where you are.

        self.trackWidget = trackWidget
        self.primaryMixdownWidget = primaryMixdownWidget
        self.secondaryMixdownWidget = secondaryMixdownWidget

        self.trackWidget.currentTextChanged.connect(self.onSignal_trackWidget_currentTextChanged)

    # def __str__(self):
    #     return '{}: id={}, index={}, track={}, primaryMixdown={}, secondaryMixdown={}'\
    #         .format(self.XMLNAME, id(self),
    #         self.index, self.track, self.primaryMixdown, self.secondaryMixdown)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.trackWidget.setCurrentText('')
        self.primaryMixdownWidget.setCurrentText('')
        self.secondaryMixdownWidget.setCurrentText('')

    @property
    def parent(self):
        return self.__parent

    def addTrackItems(self, items):
        """ Add the dropdown list items to the track widget.
        """
        UpdateComboBox(self.trackWidget, items)

    def addMixdownItems(self, items):
        """ Add the dropdown list items to both of the mixdown widgets.
        """
        UpdateComboBox(self.primaryMixdownWidget, items)
        UpdateComboBox(self.secondaryMixdownWidget, items)

    def setEnabled(self, enabled):
        """ Enable/disable all of the audio track widgets.
        """
        self.trackWidget.setEnabled(enabled)
        self.primaryMixdownWidget.setEnabled(enabled)
        self.secondaryMixdownWidget.setEnabled(enabled)

    def onSignal_trackWidget_currentTextChanged(self, text=None):
        """ Enable/disable the mixdown widgets, based on the track widget.
        """
        enableMixdowns = (self.trackWidget.isEnabled() and
            bool(self.trackWidget.currentText()))

        self.primaryMixdownWidget.setEnabled(enableMixdowns)
        self.secondaryMixdownWidget.setEnabled(enableMixdowns)

    def setTrackStateFromWidgets(self, trackState):
        """ Sets the trackState attributes from the audio track widgets.
        """
        assert(isinstance(trackState, AudioTrackState))

        trackState.track = self.trackWidget.currentText()
        trackState.primaryMixdown = self.primaryMixdownWidget.currentText()
        trackState.secondaryMixdown = self.secondaryMixdownWidget.currentText()

    def setWidgetsFromTrackState(self, trackState):
        """ Set the currentText()/selection for the audio track widgets from
            the audio track state.
        """
        assert(isinstance(trackState, AudioTrackState))

        self.trackWidget.setCurrentText(trackState.track)
        self.primaryMixdownWidget.setCurrentText(trackState.primaryMixdown)
        self.secondaryMixdownWidget.setCurrentText(trackState.secondaryMixdown)

class AudioTrackWidgetsList(MutableSequence):
    """ Container for a list of AudioTrackWidgets.
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
        assert(isinstance(obj, AudioTrackWidgets))
        self.trackWidgetsList[idx] = obj

    def __delitem__(self, idx):
        del self.trackWidgetsList[idx]

    def __len__(self):
        return len(self.trackWidgetsList)

    def insert(self, idx, obj):
        assert(isinstance(obj, AudioTrackWidgets))
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

    def enableMixdowns(self):
        """ Enable/disable the mixdown widgets for all entries in the list.
        """
        for trackWidgets in self.trackWidgetsList:
            trackWidgets.onSignal_trackWidget_currentTextChanged()

    def audioTracks(self):
        """ Return the selected audio tracks, with the associated mixdowns.
        """
        tracks = []

        for trackWidgets in self.trackWidgetsList:
            if (trackWidgets.trackWidget.currentText()):
                mixdowns = []
                if (trackWidgets.primaryMixdownWidget.currentText()):
                    mixdowns.append(trackWidgets.primaryMixdownWidget.currentText())
                if (trackWidgets.secondaryMixdownWidget.currentText()):
                    mixdowns.append(trackWidgets.secondaryMixdownWidget.currentText())
                tracks.append((trackWidgets.trackWidget.currentText(), mixdowns))

        return tracks

    def setEnabled(self, enabled):
        """ Enable/disable all of the audio track widgets.
        """
        for trackWidgets in self.trackWidgetsList:
            trackWidgets.setEnabled(enabled)

    def setTrackStatesFromWidgets(self, trackStates):
        """ Set the list of audio track states from list of widgets.
        """
        assert(isinstance(trackStates, AudioTrackStates))
        assert(len(trackStates) == len(self.trackWidgetsList))

        for idx in range(len(trackStates)):
            self.trackWidgetsList[idx].setTrackStateFromWidgets(trackStates[idx])

    def setWidgetsFromTrackStates(self, trackStates):
        """ Set the currentText()/selection for the audio track widgets from
            a list of audio track states.
        """
        assert(isinstance(trackStates, AudioTrackStates))
        assert(len(trackStates) == len(self.trackWidgetsList))

        for idx in range(len(trackStates)):
            self.trackWidgetsList[idx].setWidgetsFromTrackState(trackStates[idx])
