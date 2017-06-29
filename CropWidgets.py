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

from Crop import Crop

class CropWidgets(object):
    """ Contains the widgets for custom cropping.
    """

    def __init__(self, parent, topWidget, bottomWidget, leftWidget, rightWidget):

        self.__parent = parent

        self.topWidget = topWidget
        self.bottomWidget = bottomWidget
        self.leftWidget = leftWidget
        self.rightWidget = rightWidget

    # def __str__(self):
    #     return '{}: id={}, index={}, track={}, primaryMixdown={}, secondaryMixdown={}'\
    #         .format(self.XMLNAME, id(self),
    #         self.index, self.track, self.primaryMixdown, self.secondaryMixdown)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.topWidget.setValue(0)
        self.bottomWidget.setValue(0)
        self.leftWidget.setValue(0)
        self.rightWidget.setValue(0)

    @property
    def parent(self):
        return self.__parent

    def setEnabled(self, enabled):
        """ Enable/disable all of the audio track widgets.
        """
        self.topWidget.setEnabled(enabled)
        self.bottomWidget.setEnabled(enabled)
        self.leftWidget.setEnabled(enabled)
        self.rightWidget.setEnabled(enabled)

    def setCropFromWidgets(self, crop):
        """ Sets the crop object attributes from the crop widgets.
        """
        assert(isinstance(crop, Crop))

        crop.top = self.topWidget.value()
        crop.bottom = self.bottomWidget.value()
        crop.left = self.leftWidget.value()
        crop.right = self.rightWidget.value()

    def setWidgetsFromCrop(self, crop):
        """ Set the value for the audio track widgets from the crop state.
        """
        assert(isinstance(crop, Crop))

        self.topWidget.setValue(crop.top)
        self.bottomWidget.setValue(crop.bottom)
        self.leftWidget.setValue(crop.left)
        self.rightWidget.setValue(crop.right)
