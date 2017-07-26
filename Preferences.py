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

import os, os.path, sys, xml.dom, xml.dom.minidom as minidom

from collections import MutableSequence

sys.path.insert(0, '../Helpers')

import XMLHelpers
from SingletonLog import SingletonLog

class Executables(object):
    """ Store the information about the executables location(s) and any default
        command line settings.
    """

    XMLNAME = 'Executables'

    if (sys.platform == 'win32'):
        DEFAULT_CLI = os.path.join(os.getcwd(), 'HandBrakeCLI.exe')
        DEFAULT_VLC = os.path.join(os.getcwd(), 'VLC.exe')
    else:
        DEFAULT_CLI = 'HandBrakeCLI'
        DEFAULT_VLC = 'vlc'

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: handBrakeCLI="{}, VLC="{}"\n'.format(self.XMLNAME,
            self.handBrakeCLI, self.VLC)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.handBrakeCLI = self.DEFAULT_CLI
        self.VLC = self.DEFAULT_VLC

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.clear()

        # This attribute was renamed as part of the QT conversion.
        self.handBrakeCLI = XMLHelpers.GetXMLAttributes(element,
            ['handBrakeCLI', 'CLIPath'], self.DEFAULT_CLI)

        self.VLC = XMLHelpers.GetXMLAttribute(element, 'VLC', self.DEFAULT_VLC)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('handBrakeCLI', self.handBrakeCLI.strip())
        element.setAttribute('VLC', self.VLC.strip())

        return element

class Logging(object):
    """ Stores users information about log settings.
    """
    XMLNAME = 'Logging'

    DEFAULT_ANALYSIS = False
    DEFAULT_COMMANDS_AND_TIMESTAMPS = False
    DEFAULT_FILENAME = ''

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: log source analysis={}, log command and timestamps={}, log file="{}"\n'\
            .format(self.XMLNAME, self.analysis, self.commandsAndTimestamps, self.filename)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.analysis = self.DEFAULT_ANALYSIS
        self.commandsAndTimestamps = self.DEFAULT_COMMANDS_AND_TIMESTAMPS
        self.filename = self.DEFAULT_FILENAME

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.clear()

        self.analysis = XMLHelpers.GetXMLAttributeAsBool(element, 'Analysis', self.DEFAULT_ANALYSIS)
        self.commandsAndTimestamps = XMLHelpers.GetXMLAttributeAsBool(element, 'CommandsAndTimestamps', self.DEFAULT_COMMANDS_AND_TIMESTAMPS)
        self.filename = XMLHelpers.GetXMLAttribute(element, 'Filename', self.DEFAULT_FILENAME)

    def initializeLog(self):
        """ Open the log file, if the options require one.
            The file will be created if it does not exist.
        """
        log = SingletonLog()

        if (self.filename):
            log.open(self.filename)
            return

        log.close()

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('Analysis', XMLHelpers.BoolToString(self.analysis))
        element.setAttribute('CommandsAndTimestamps', XMLHelpers.BoolToString(self.commandsAndTimestamps))
        element.setAttribute('Filename', self.filename.strip())

        return element

class Options(object):
    """ Stores the information about general option settings.
    """
    XMLNAME = 'Options'

    DEFAULT_NUMBER_CHAPTER_NAMES = False
    DEFAULT_CHECK_MP4_AUDIO = False
    DEFAULT_CHECK_IMPORT_SHORT_CHAPTER = False
    DEFAULT_TEXT_IMPORT_SHORT_CHAPTER = 'end of title'

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: numberChapterNames="{}"\n' \
        'checkMp4Audio="{}"\n' \
        'checkImportShortChapter = "{}", textImportShortChapter="{}"'.format(self.XMLNAME,
        self.numberChapterNames, self.checkMp4Audio,
        self.checkImportShortChapter, self.textImportShortChapter)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.numberChapterNames = self.DEFAULT_NUMBER_CHAPTER_NAMES
        self.checkMp4Audio = self.DEFAULT_CHECK_MP4_AUDIO
        self.checkImportShortChapter = self.DEFAULT_CHECK_IMPORT_SHORT_CHAPTER
        self.textImportShortChapter = self.DEFAULT_TEXT_IMPORT_SHORT_CHAPTER

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.clear()

        self.numberChapterNames = XMLHelpers.GetXMLAttributeAsBool(element, 'NumberChapterNames', self.DEFAULT_NUMBER_CHAPTER_NAMES)
        self.checkMp4Audio = XMLHelpers.GetXMLAttributeAsBool(element, 'CheckMP4Audio', self.DEFAULT_CHECK_MP4_AUDIO)
        self.checkImportShortChapter = XMLHelpers.GetXMLAttributeAsBool(element, 'CheckImportShortChapter', self.DEFAULT_CHECK_IMPORT_SHORT_CHAPTER)
        self.textImportShortChapter = XMLHelpers.GetXMLAttribute(element, 'TextImportShortChapter', self.DEFAULT_TEXT_IMPORT_SHORT_CHAPTER)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('NumberChapterNames', XMLHelpers.BoolToString(self.numberChapterNames))
        element.setAttribute('CheckMP4Audio', XMLHelpers.BoolToString(self.checkMp4Audio))
        element.setAttribute('CheckImportShortChapter', XMLHelpers.BoolToString(self.checkImportShortChapter))
        element.setAttribute('TextImportShortChapter', self.textImportShortChapter.strip())

        return element

class FilenameTemplates(MutableSequence):
    """ A list of the templates used to generate a file name.
    """
    XMLNAME = 'FilenameTemplates'

    TITLE_KEY                   = '<title>'
    PRESET_KEY                  = '<preset>'
    AUDIO_CODEC_KEY             = '<acodec>'
    EPISODE_NUMBER_KEY          = '<epno>'
    EPISODE_TITLE_KEY           = '<eptitle>'
    CHAPTER_RANGE_EPISODE_KEY   = '<cetitle>'

    SPACES_TO_UNDERSCORE_FLAG   = '<$_>'

    DEFAULT_FILENAME_TEMPLATES = [
        '<title>.mkv',
        '<title>.mp4',
        '<eptitle>.mkv',
        '<cetitle>.mkv',
        '<title><epno> - <eptitle>.mkv',
        '<title> - <eptitle>.mkv',
        '<title> [<preset>][<acodec>].mkv',
    ]

    @classmethod
    def buildFilename(cls, filenameTemplate, title, presetTag, audioTag, episodeNumber, episodeTitle, chapterEpisodeTitle):
        """ Build the file name using the preset values.
        """
        filename = filenameTemplate

        filename = filename.replace(cls.TITLE_KEY,                  title)
        filename = filename.replace(cls.PRESET_KEY,                 presetTag)
        filename = filename.replace(cls.AUDIO_CODEC_KEY,            audioTag)
        filename = filename.replace(cls.EPISODE_NUMBER_KEY,         episodeNumber)
        filename = filename.replace(cls.EPISODE_TITLE_KEY,          episodeTitle)
        filename = filename.replace(cls.CHAPTER_RANGE_EPISODE_KEY,  chapterEpisodeTitle)

        # Flag that will cause all spaces with to be replaced with underscores
        if (cls.SPACES_TO_UNDERSCORE_FLAG in filenameTemplate):
            filename = filename.replace(cls.SPACES_TO_UNDERSCORE_FLAG, '')                    # remove the flag
            filename = filename.replace(' ', '_')

        return filename

    @classmethod
    def hasTitleKey(cls, filenameTemplate):
        return (cls.TITLE_KEY in filenameTemplate)

    @classmethod
    def hasEpisodeTitleKey(cls, filenameTemplate):
        return (cls.EPISODE_TITLE_KEY in filenameTemplate)

    @classmethod
    def hasChapterRangeEpisodeKey(cls, filenameTemplate):
        return (cls.CHAPTER_RANGE_EPISODE_KEY in filenameTemplate)

    @classmethod
    def isMP4(cls, filenameTemplate):
        root, ext = os.path.splitext(filenameTemplate)
        return (ext.lower() == '.mp4')

    def __init__(self, parent):
        self.__parent = parent

        self.filenameTemplates = []

        self.setDefaults()

    def __str__(self):
        return '{}:\n    {}\n'.format(self.XMLNAME,
            '\n    '.join(self.filenameTemplates))

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.filenameTemplates[idx]

    def __setitem__(self, idx, obj):
        self.filenameTemplates[idx] = obj

    def __delitem__(self, idx):
        del self.filenameTemplates[idx]

    def __len__(self):
        return len(self.filenameTemplates)

    def insert(self, idx, obj):
        self.filenameTemplates.insert(idx, obj)
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """
        del self.filenameTemplates[:]

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.clear()

        for childNode in element.childNodes:
            if (childNode.localName == 'FilenameTemplate'):
                if (childNode.hasAttribute('Value')):
                    self.filenameTemplates.append(XMLHelpers.GetXMLAttribute(childNode, 'Value'))

        if (not len(self.filenameTemplates)):
            self.setDefaults()

    def setDefaults(self):
        """ Set the default values.
        """
        self.clear()
        for default in self.DEFAULT_FILENAME_TEMPLATES:
            self.append(default)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        groupElement = doc.createElement(self.XMLNAME)
        parentElement.appendChild(groupElement)

        # These are "convenience" attributes for other applications that read the XML file.
        # They are ignored by self.fromXML().
        groupElement.setAttribute('count', str(len(self.filenameTemplates)))

        for filenameTemplate in self.filenameTemplates:
            element = doc.createElement('FilenameTemplate')
            element.setAttribute('Value', filenameTemplate.strip())
            groupElement.appendChild(element)

        return groupElement

class NewSource(object):
    """ Actions to take when the source changes.
    """
    XMLNAME = 'NewSource'

    DEFAULT_FIRST_MASK = True
    DEFAULT_FIRST_PRESET = True
    DEFAULT_USE_DEFAULT_DESTINATION = True
    DEFAULT_DEFAULT_DESTINATION = ''

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: firstMask={}, firstPreset={}\n'\
            .format(self.XMLNAME, str(self.firstMask), str(self.firstPreset))

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.firstMask = self.DEFAULT_FIRST_MASK
        self.firstPreset = self.DEFAULT_FIRST_PRESET

        self.useDefaultDestination = self.DEFAULT_USE_DEFAULT_DESTINATION
        self.defaultDestination = self.DEFAULT_DEFAULT_DESTINATION

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, newSourceElement):
        """ Initialize the object from an XML element.
        """
        self.firstMask = XMLHelpers.GetXMLAttributeAsBool(newSourceElement, 'FirstMask', self.DEFAULT_FIRST_MASK)
        self.firstPreset = XMLHelpers.GetXMLAttributeAsBool(newSourceElement, 'FirstPreset', self.DEFAULT_FIRST_PRESET)

        self.useDefaultDestination = XMLHelpers.GetXMLAttributeAsBool(newSourceElement, 'UseDefaultDestination', self.DEFAULT_USE_DEFAULT_DESTINATION)
        self.defaultDestination = XMLHelpers.GetXMLAttribute(newSourceElement, 'DefaultDestination', self.DEFAULT_DEFAULT_DESTINATION)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('FirstMask', XMLHelpers.BoolToString(self.firstMask))
        element.setAttribute('FirstPreset', XMLHelpers.BoolToString(self.firstPreset))

        element.setAttribute('UseDefaultDestination', XMLHelpers.BoolToString(self.useDefaultDestination))
        element.setAttribute('DefaultDestination', self.defaultDestination)

        return element

class FilenameReplacement(object):
    """ Options for replacing characters in a filename.
    """
    XMLNAME = 'FilenameReplacement'

    DEFAULT_REPLACE_FILENAME_CHARACTERS = False
    DEFAULT_FILENAME_CHARACTERS_TO_REPLACE = '\\/:*?\'<>|'
    DEFAULT_REPLACEMENT_FILENAME_CHARACTER = '_'

    def __init__(self, parent):
        self.__parent = parent

        self.clear()

    def __str__(self):
        return '{}: replaceFilenameCharacters={}, filenameCharactersToReplace="{}", replacementFilenameCharacter="{}"\n'\
            .format(self.XMLNAME, self.replaceFilenameCharacters, self.filenameCharactersToReplace,
            self.replacementFilenameCharacter)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.replaceFilenameCharacters = self.DEFAULT_REPLACE_FILENAME_CHARACTERS
        self.filenameCharactersToReplace = self.DEFAULT_FILENAME_CHARACTERS_TO_REPLACE
        self.replacementFilenameCharacter = self.DEFAULT_REPLACEMENT_FILENAME_CHARACTER

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.replaceFilenameCharacters = XMLHelpers.GetXMLAttributeAsBool(element, 'ReplaceFilenameCharacters', self.DEFAULT_REPLACE_FILENAME_CHARACTERS)
        self.filenameCharactersToReplace = XMLHelpers.GetXMLAttribute(element, 'FilenameCharactersToReplace', self.DEFAULT_FILENAME_CHARACTERS_TO_REPLACE)
        self.replacementFilenameCharacter = XMLHelpers.GetXMLAttribute(element, 'ReplacementFilenameCharacter', self.DEFAULT_REPLACEMENT_FILENAME_CHARACTER)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('ReplaceFilenameCharacters', XMLHelpers.BoolToString(self.replaceFilenameCharacters))
        element.setAttribute('FilenameCharactersToReplace', self.filenameCharactersToReplace.strip())
        element.setAttribute('ReplacementFilenameCharacter', self.replacementFilenameCharacter.strip())

        return element

class AutoCrop(object):
    """ Stores information about the automatic cropping options.
    """
    XMLNAME = 'AutoCrop'

    DEFAULT_AUTORESET_CROP = True
    DEFAULT_AUTOCOPY_CROP = True

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: autoResetCrop={}  autoCopyCrop={}\n'\
            .format(self.XMLNAME, self.autoResetCrop, self.autoCopyCrop)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.autoResetCrop = self.DEFAULT_AUTORESET_CROP
        self.autoCopyCrop = self.DEFAULT_AUTOCOPY_CROP

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.autoResetCrop = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoResetCrop', self.DEFAULT_AUTORESET_CROP)
        self.autoCopyCrop = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoCopyCrop', self.DEFAULT_AUTOCOPY_CROP)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('AutoResetCrop', XMLHelpers.BoolToString(self.autoResetCrop))
        element.setAttribute('AutoCopyCrop', XMLHelpers.BoolToString(self.autoCopyCrop))

        return element

class AutoTitle(object):
    """ Options that control the automatic title selection and which titles are
        displayed.
    """
    XMLNAME = 'AutoTitle'

    DEFAULT_AUTOSELECT_LONGEST_TITLE = True
    DEFAULT_MINIMUM_TITLE_SECONDS = 30

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: autoSelectLongestTitle={}, minimumTitleSeconds={}\n'\
            .format(self.XMLNAME, self.autoSelectLongestTitle, self.minimumTitleSeconds)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.autoSelectLongestTitle = self.DEFAULT_AUTOSELECT_LONGEST_TITLE
        self.minimumTitleSeconds = self.DEFAULT_MINIMUM_TITLE_SECONDS

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.autoSelectLongestTitle = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoSelectLongestTitle', self.DEFAULT_AUTOSELECT_LONGEST_TITLE)
        self.minimumTitleSeconds = XMLHelpers.GetXMLAttributeAsInt(element, 'MinimumTitleSeconds', self.DEFAULT_MINIMUM_TITLE_SECONDS)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('AutoSelectLongestTitle', XMLHelpers.BoolToString(self.autoSelectLongestTitle))
        element.setAttribute('MinimumTitleSeconds', str(self.minimumTitleSeconds))

        return element

class AutoAudioTracks(object):
    """ Options that control the automatic selection of audio tracks when the
        source changes.
    """
    XMLNAME = 'AutoAudioTracks'

    DEFAULT_AUTOSELECT_PREFERRED_LANGUAGE = False
    DEFAULT_PREFERRED_LANGUAGE = ''

    DEFAULT_AUTOSELECT_51 = True
    DEFAULT_AUTOSELECT_DTS = False
    DEFAULT_AUTOSELECT_FALLBACK = True

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: autoSelectPreferredLanguage={}, preferredLanguage="{}", autoSelect51={}, autoSelectDTS={}, autoSelectFallback={}\n'\
            .format(self.XMLNAME, self.autoSelectPreferredLanguage, self.preferredLanguage,
            self.autoSelect51, self.autoSelectDTS, self.autoSelectFallback)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.autoSelectPreferredLanguage = self.DEFAULT_AUTOSELECT_PREFERRED_LANGUAGE
        self.preferredLanguage = self.DEFAULT_PREFERRED_LANGUAGE

        self.autoSelect51 = self.DEFAULT_AUTOSELECT_51
        self.autoSelectDTS = self.DEFAULT_AUTOSELECT_DTS
        self.autoSelectFallback = self.DEFAULT_AUTOSELECT_FALLBACK

    @property
    def autoSelect(self):
        """ Return True if any of the autoselect attributes are true.
        """
        return (self.autoSelect51 or self.autoSelectDTS or
            self.DEFAULT_AUTOSELECT_FALLBACK)

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.autoSelectPreferredLanguage = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoSelectPreferredLanguage', self.DEFAULT_AUTOSELECT_PREFERRED_LANGUAGE)
        self.preferredLanguage = XMLHelpers.GetXMLAttribute(element, 'PreferredLanguage', self.DEFAULT_PREFERRED_LANGUAGE)

        self.autoSelect51 = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoSelect51', self.DEFAULT_AUTOSELECT_51)
        self.autoSelectDTS = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoSelectDTS', self.DEFAULT_AUTOSELECT_DTS)
        self.autoSelectFallback = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoSelectFallback', self.DEFAULT_AUTOSELECT_FALLBACK)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('AutoSelectPreferredLanguage', XMLHelpers.BoolToString(self.autoSelectPreferredLanguage))
        element.setAttribute('PreferredLanguage', self.preferredLanguage.strip())

        element.setAttribute('AutoSelect51', XMLHelpers.BoolToString(self.autoSelect51))
        element.setAttribute('AutoSelectDTS', XMLHelpers.BoolToString(self.autoSelectDTS))
        element.setAttribute('AutoSelectFallback', XMLHelpers.BoolToString(self.autoSelectFallback))

        return element

class AutoSubtitle(object):
    """ Options that control the automatic selection of subtitle tracks when
        the source changes.
    """
    XMLNAME = 'AutoSubtitle'

    DEFAULT_AUTOSELECT_PREFERRED_LANGUAGE = False
    DEFAULT_PREFERRED_LANGUAGE = ''

    DEFAULT_AUTOSELECT_SUBTITLE = True
    DEFAULT_SUBTITLE_BURN = False
    DEFAULT_SUBTITLE_DEFAULT = False

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: autoSelectPreferredLanguage={}, preferredLanguage="{}", autoSelectSubtitle={}, subtitleBurn={}, subtitleDefault={}\n'\
            .format(self.XMLNAME, self.autoSelectPreferredLanguage, self.preferredLanguage,
            self.autoSelectSubtitle, self.subtitleBurn, self.subtitleDefault)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.autoSelectPreferredLanguage = self.DEFAULT_AUTOSELECT_PREFERRED_LANGUAGE
        self.preferredLanguage = self.DEFAULT_PREFERRED_LANGUAGE

        self.autoSelectSubtitle = self.DEFAULT_AUTOSELECT_SUBTITLE
        self.subtitleBurn = self.DEFAULT_SUBTITLE_BURN
        self.subtitleDefault = self.DEFAULT_SUBTITLE_DEFAULT

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.autoSelectPreferredLanguage = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoSelectPreferredLanguage', self.DEFAULT_AUTOSELECT_PREFERRED_LANGUAGE)
        self.preferredLanguage = XMLHelpers.GetXMLAttribute(element, 'PreferredLanguage', self.DEFAULT_PREFERRED_LANGUAGE)

        self.autoSelectSubtitle = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoSelectSubtitle', self.DEFAULT_AUTOSELECT_SUBTITLE)
        self.subtitleBurn = XMLHelpers.GetXMLAttributeAsBool(element, 'SubtitleBurn', self.DEFAULT_SUBTITLE_BURN)
        self.subtitleDefault = XMLHelpers.GetXMLAttributeAsBool(element, 'SubtitleDefault', self.DEFAULT_SUBTITLE_DEFAULT)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('AutoSelectPreferredLanguage', XMLHelpers.BoolToString(self.autoSelectPreferredLanguage))
        element.setAttribute('PreferredLanguage', self.preferredLanguage.strip())

        element.setAttribute('AutoSelectSubtitle', XMLHelpers.BoolToString(self.autoSelectSubtitle))
        element.setAttribute('SubtitleBurn', XMLHelpers.BoolToString(self.subtitleBurn))
        element.setAttribute('SubtitleDefault', XMLHelpers.BoolToString(self.subtitleDefault))

        return element

class AutoMixdown(object):
    """ Options that control the automatic selection of a mixdown for an audio
        track when the source changes.
    """
    XMLNAME = 'AutoMixdown'

    DEFAULT_CHOICE = 'None'

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: ac351Primary="{}", ac351Secondary="{}", ' \
            'dtsPrimary="{}", dtsSecondary="{}", ' \
            'dtshdPrimary="{}", dtshdSecondary="{}", ' \
            'ac3Primary="{}", ac3Secondary="{}", ' \
            'otherPrimary="{}", otherSecondary="{}"\n'\
            .format(self.XMLNAME,
            self.ac351Primary, self.ac351Secondary,
            self.dtsPrimary, self.dtsSecondary,
            self.dtshdPrimary, self.dtshdSecondary,
            self.ac3Primary, self.ac3Secondary,
            self.otherPrimary, self.otherSecondary)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.ac351Primary = self.DEFAULT_CHOICE
        self.ac351Secondary = self.DEFAULT_CHOICE

        self.dtsPrimary = self.DEFAULT_CHOICE
        self.dtsSecondary = self.DEFAULT_CHOICE

        self.dtshdPrimary = self.DEFAULT_CHOICE
        self.dtshdSecondary = self.DEFAULT_CHOICE

        self.ac3Primary = self.DEFAULT_CHOICE
        self.ac3Secondary = self.DEFAULT_CHOICE

        self.otherPrimary = self.DEFAULT_CHOICE
        self.otherSecondary = self.DEFAULT_CHOICE

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.ac351Primary = XMLHelpers.GetXMLAttribute(element, 'AC351Primary', self.DEFAULT_CHOICE)
        self.ac351Secondary = XMLHelpers.GetXMLAttribute(element, 'AC351Secondary', self.DEFAULT_CHOICE)

        self.dtsPrimary = XMLHelpers.GetXMLAttribute(element, 'DTSPrimary', self.DEFAULT_CHOICE)
        self.dtsSecondary = XMLHelpers.GetXMLAttribute(element, 'DTSSecondary', self.DEFAULT_CHOICE)

        self.dtshdPrimary = XMLHelpers.GetXMLAttribute(element, 'DTSHDPrimary', self.DEFAULT_CHOICE)
        self.dtshdSecondary = XMLHelpers.GetXMLAttribute(element, 'DTSHDSecondary', self.DEFAULT_CHOICE)

        self.ac3Primary = XMLHelpers.GetXMLAttribute(element, 'AC3Primary', self.DEFAULT_CHOICE)
        self.ac3Secondary = XMLHelpers.GetXMLAttribute(element, 'AC3Secondary', self.DEFAULT_CHOICE)

        self.otherPrimary = XMLHelpers.GetXMLAttribute(element, 'OtherPrimary', self.DEFAULT_CHOICE)
        self.otherSecondary = XMLHelpers.GetXMLAttribute(element, 'OtherSecondary', self.DEFAULT_CHOICE)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('AC351Primary', self.ac351Primary)
        element.setAttribute('AC351Secondary', self.ac351Secondary)

        element.setAttribute('DTSPrimary', self.dtsPrimary)
        element.setAttribute('DTSSecondary', self.dtsSecondary)

        element.setAttribute('DTSHDPrimary', self.dtshdPrimary)
        element.setAttribute('DTSHDSecondary', self.dtshdSecondary)

        element.setAttribute('AC3Primary', self.ac3Primary)
        element.setAttribute('AC3Secondary', self.ac3Secondary)

        element.setAttribute('OtherPrimary', self.otherPrimary)
        element.setAttribute('OtherSecondary', self.otherSecondary)

        return element

class Preset(object):
    """ Preset transcoding options for HandBrake.
    """
    XMLNAME = 'Preset'

    DEFAULT_NAME = ''
    DEFAULT_TAG = ''
    DEFAULT_SETTINGS = ''

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: name="{}", tag="{}"\n  settings="{}"\n'\
            .format(self.XMLNAME, self.name, self.tag, self.settings)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.name = self.DEFAULT_NAME
        self.tag = self.DEFAULT_TAG
        self.settings = self.DEFAULT_SETTINGS

    @property
    def parent(self):
        return self.__parent

    @property
    def simpleSettings(self):
        """ Returns the settings attribute with new lines (\n), carriage returns (\r),
            and multiple spaces stripped out.
        """
        s = self.settings.replace('\n', ' ')
        s = s.replace('\r', ' ')
        while ('  ' in s):
            s = s.replace('  ', ' ')

        return s

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.name = XMLHelpers.GetXMLAttribute(element, 'Name', self.DEFAULT_NAME)
        self.tag = XMLHelpers.GetXMLAttribute(element, 'Tag', self.DEFAULT_TAG)
        self.settings = XMLHelpers.GetXMLAttribute(element, 'Settings', self.DEFAULT_SETTINGS)

    def setParent(self, parent):
        """ This should only be used by the Mixdowns class to update the objects
            parent.
        """
        assert(isinstance(parent, Presets))

        self.__parent = parent

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement('Preset')
        parentElement.appendChild(element)

        element.setAttribute('Name', self.name.strip())
        element.setAttribute('Tag', self.tag.strip())
        element.setAttribute('Settings', self.settings.strip())

        return element

class Presets(MutableSequence):
    """ Preset transcoding options for HandBrake.
    """
    XMLNAME = 'Presets'

    DEFAULT_PRESETS = [
        ['Film',      'Film',    '--detelecine --decomb --auto-anamorphic --modulus 16 -e x264 -q 20 --vfr --x264-preset=slow   --x264-profile=high --x264-tune="film"      --h264-level="4.1" -v 1'],
        ['Animation', 'Anime',   '--detelecine --decomb --auto-anamorphic --modulus 16 -e x264 -q 20 --vfr --x264-preset=slow   --x264-profile=high --x264-tune="animation" --h264-level="4.1" -v 1'],
        ['Trailer',   'Trailer', '--detelecine --decomb --auto-anamorphic --modulus 16 -e x264 -q 24 --vfr --x264-preset=medium --x264-profile=main --x264-tune="film"      --h264-level="4.1" -v 1'],
        ['Extra',     'Extra',   '--detelecine --decomb --modulus 16 -e x264 -q 22 --vfr --encoder-preset=faster  --encoder-profile=main  --encoder-tune="film"  --encoder-level="4.1" -v 1']
    ]

    def __init__(self,parent):
        self.__parent = parent

        self.presets = []
        self.presetsByName = {}

        self.setDefaults()

    def __str__(self):
        return '{}: len: {}'.format(self.XMLNAME, len(self.presets))

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.presets[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, Preset))

        self.presetsByName.pop(self.presets[idx].name)
        self.presets[idx] = obj
        self.presetsByName[obj.name] = obj

    def __delitem__(self, idx):
        self.presetsByName.pop(self.presets[idx].name)
        del self.presets[idx]

    def __len__(self):
        return len(self.presets)

    def insert(self, idx, obj):
        assert(isinstance(obj, Preset))

        obj.setParent(self)
        self.presets.insert(idx, obj)
        self.presetsByName[obj.name] = obj
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """
        del self.presets[:]
        self.presetsByName.clear()

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.clear()

        for childNode in element.childNodes:
            if (childNode.localName == Preset.XMLNAME):

                preset = Preset(self)
                preset.fromXML(childNode)
                self.append(preset)

        if (not len(self.presets)):
            self.setDefaults()

    def getByName(self, name):
        """ Return the preset with the given name.
        """
        return self.presetsByName[name]

    def getNames(self):
        """ Returns a list of preset names.
        """
        return self.presetsByName.keys()

    def hasName(self, presetName):
        """ Returns true if the preset name is found.
        """
        return (presetName in self.presetsByName.keys())

    def newPreset(self):
        """ Create a new Preset object and initialize it to the first default.
        """
        preset = Preset(self)
        preset.name, preset.tag, preset.settings = self.DEFAULT_PRESETS[0]
        return preset

    def setDefaults(self):
        """ Set the default values.
        """
        self.clear()
        for default in self.DEFAULT_PRESETS:
            preset = Preset(self)
            preset.name, preset.tag, preset.settings = default
            self.append(preset)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        # These are "convenience" attributes for other applications that read the XML file.
        # They are ignored by self.fromXML().
        element.setAttribute('count', str(len(self.presets)))

        for preset in self.presets:
            preset.toXML(doc, element)

        return element

class Mixdown(object):
    """ Store the information for a single audio mixdown.
    """
    XMLNAME = 'Mixdown'

    DEFAULT_NAME = ''
    DEFAULT_TAG = ''
    DEFAULT_ENCODER = ''
    DEFAULT_MIXDOWN = ''
    DEFAULT_SAMPLE_RATE = ''
    DEFAULT_BITRATE = ''
    DEFAULT_DYNAMIC_RANGE_COMPRESSION = ''
    DEFAULT_GAIN = ''

    def __init__(self, parent):
        self.__parent = parent        # The parent is usually the 'Mixdowns' container
        self.clear()

    def __str__(self):
        return '{}: name="{}", tag="{}"\n  encoder="{}", mixdown="{}"\n  sampleRate="{}", bitrate="{}", drc="{}", gain="{}"\n'\
            .format(self.XMLNAME, self.name, self.tag, self.encoder, self.mixdown,
            self.sampleRate, self.bitrate, self.dynamicRangeCompression, self.gain)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.name = self.DEFAULT_NAME
        self.tag = self.DEFAULT_TAG
        self.encoder = self.DEFAULT_ENCODER
        self.mixdown = self.DEFAULT_MIXDOWN
        self.sampleRate = self.DEFAULT_SAMPLE_RATE
        self.bitrate = self.DEFAULT_BITRATE
        self.dynamicRangeCompression = self.DEFAULT_DYNAMIC_RANGE_COMPRESSION
        self.gain = self.DEFAULT_GAIN

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.name = XMLHelpers.GetXMLAttribute(element, 'Name', self.DEFAULT_NAME)
        self.tag  = XMLHelpers.GetXMLAttribute(element, 'Tag', self.DEFAULT_TAG)
        self.encoder = XMLHelpers.GetXMLAttribute(element, 'Encoder', self.DEFAULT_ENCODER)
        self.mixdown = XMLHelpers.GetXMLAttribute(element, 'Mixdown', self.DEFAULT_MIXDOWN)
        self.sampleRate = XMLHelpers.GetXMLAttribute(element, 'SampleRate', self.DEFAULT_SAMPLE_RATE)
        self.bitrate = XMLHelpers.GetXMLAttribute(element, 'Bitrate', self.DEFAULT_BITRATE)
        self.dynamicRangeCompression = XMLHelpers.GetXMLAttribute(element, 'DRC', self.DEFAULT_DYNAMIC_RANGE_COMPRESSION)
        self.gain = XMLHelpers.GetXMLAttribute(element, 'Gain', self.DEFAULT_GAIN)

    def setParent(self, parent):
        """ This should only be used by the Mixdowns class to update the objects parent.
        """
        assert(isinstance(parent, Mixdowns))

        self.__parent = parent

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('Name', self.name.strip())
        element.setAttribute('Tag', self.tag.strip())
        element.setAttribute('Encoder', self.encoder.strip())
        element.setAttribute('Mixdown', self.mixdown.strip())
        element.setAttribute('SampleRate', self.sampleRate.strip())
        element.setAttribute('Bitrate', self.bitrate.strip())
        element.setAttribute('DRC', self.dynamicRangeCompression.strip())
        element.setAttribute('Gain', self.gain.strip())

        return element

class Mixdowns(MutableSequence):
    """ A list of the available mixdowns.
    """
    XMLNAME = 'Mixdowns'

    DEFAULT_MIXDOWNS = [
        ('COPYAC3', 'AC3', 'copy:ac3', 'auto', 'Auto', '0', '0.0', '0'),
        ('COPYDTS', 'DTS', 'copy:dts', 'auto', 'Auto', '0', '0.0', '0'),
        ('COPYDTSHD', 'DTSHD', 'copy:dtshd', 'auto', 'Auto', '0', '0.0', '0'),
        ('AAC 5.1', 'AAC', 'av_aac', '5point1', 'Auto', '192', '0.0', '0'),
        ('AAC DPL2', 'AAC', 'av_aac', 'dpl2', 'Auto', '192', '0.0', '0')
    ]

    def __init__(self, parent):
        self.__parent = parent

        self.mixdowns = []
        self.mixdownsByName = {}

        self.setDefaults()

    def __str__(self):
        return '{}: len: {}'.format(self.XMLNAME, len(self.mixdowns))

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.mixdowns[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, Mixdown))

        self.mixdownsByName.pop(self.mixdowns[idx].name)
        self.mixdowns[idx] = obj
        self.mixdownsByName[obj.name] = obj

    def __delitem__(self, idx):
        self.mixdownsByName.pop(self.mixdowns[idx].name)
        del self.mixdowns[idx]

    def __len__(self):
        return len(self.mixdowns)

    def insert(self, idx, obj):
        assert(isinstance(obj, Mixdown))

        obj.setParent(self)
        self.mixdowns.insert(idx, obj)
        self.mixdownsByName[obj.name] = obj
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """
        del self.mixdowns[:]
        self.mixdownsByName.clear()

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, mixdownsElement):
        """ Initialize the object from an XML element.
        """
        self.clear()

        for childNode in mixdownsElement.childNodes:
            if (childNode.localName == Mixdown.XMLNAME):
                mixdown = Mixdown(self)
                mixdown.fromXML(childNode)
                self.append(mixdown)

        if (not len(self.mixdowns)):
            self.setDefaults()

    def getByName(self, name):
        """ Returns the mixdown object for a name.
            Returns None if the requested object doesn't exist.
        """
        if (name in self.mixdownsByName.keys()):
            return self.mixdownsByName[name]

        return None

    def getMixdowns(self):
        """ Returns a list of mixdowns.
        """
        return self.mixdownsByName.keys()

    def hasName(self, name):
        """ Returns true/false if a mixdown exists.
        """
        return (name in self.mixdownsByName.keys())

    def newMixdown(self):
        """ Create a new Mixdown object and initialize it to the first default.
        """
        mixdown = Mixdown(self)

        mixdown.name, mixdown.tag, mixdown.encoder, mixdown.mixdown, \
        mixdown.sampleRate, mixdown.bitrate, mixdown.dynamicRangeCompression, \
        mixdown.gain = self.DEFAULT_MIXDOWNS[0]

        return mixdown

    def setDefaults(self):
        """ Set the default values.
        """
        self.clear()
        for default in self.DEFAULT_MIXDOWNS:
            mixdown = Mixdown(self)
            mixdown.name, mixdown.tag, mixdown.encoder, mixdown.mixdown, mixdown.sampleRate, mixdown.bitrate, mixdown.dynamicRangeCompression, mixdown.gain = default
            self.append(mixdown)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        groupElement = doc.createElement(self.XMLNAME)
        parentElement.appendChild(groupElement)

        # These are "convenience" attributes for other applications that read the XML file.
        # They are ignored by self.fromXML().
        groupElement.setAttribute('count', str(len(self.mixdowns)))

        for mixdown in self.mixdowns:
            mixdown.toXML(doc, groupElement)

        return groupElement

class DiscSession(object):
    """ Stores information about disc session settings.
    """
    XMLNAME = 'DiscSession'

    DEFAULT_AUTO_DISC_SESSIONS = False
    DEFAULT_AUTO_DISC_SESSIONS_FOLDER = ''
    DEFAULT_AUTO_DISC_SESSIONS_PREFIX = ''

    DEFAULT_KEEP_POSITION = False
    DEFAULT_KEEP_SIZE = False
    DEFAULT_KEEP_DESTINATION = False

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: auto disc sessions={}, disc sessions folder="{}", disc sessins prefix="{}"\n  keep position={}, keep size={}, keep destination={}\n'\
            .format(self.XMLNAME, self.autoDiscSessions, self.autoDiscSessionsFolder,
            self.autoDiscSessionsPrefix, self.keepPosition, self.keepSize, self.keepDestination)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.autoDiscSessions = self.DEFAULT_AUTO_DISC_SESSIONS
        self.autoDiscSessionsFolder = self.DEFAULT_AUTO_DISC_SESSIONS_FOLDER
        self.autoDiscSessionsPrefix = self.DEFAULT_AUTO_DISC_SESSIONS_PREFIX

        self.keepPosition = self.DEFAULT_KEEP_POSITION
        self.keepSize = self.DEFAULT_KEEP_SIZE
        self.keepDestination = self.DEFAULT_KEEP_DESTINATION

    @property
    def parent(self):
        return self.__parent

    def getFullFilename(self, filename):
        """ Return the disc session filename with the folde and/or prefix added.
        """
        if (self.autoDiscSessionsPrefix):
            filename = self.autoDiscSessionsPrefix + filename

        if (self.autoDiscSessionsFolder):
            filename = os.path.join(self.autoDiscSessionsFolder, filename)

        return filename

    def fromXML(self, element):
        """ Initialize the object from an XML element.
        """
        self.autoDiscSessions = XMLHelpers.GetXMLAttributeAsBool(element, 'AutoDiscSessions', self.DEFAULT_AUTO_DISC_SESSIONS)
        self.autoDiscSessionsFolder = XMLHelpers.GetXMLAttribute(element, 'AutoDiscSessionsFolder', self.DEFAULT_AUTO_DISC_SESSIONS_FOLDER)
        self.autoDiscSessionsPrefix = XMLHelpers.GetXMLAttribute(element, 'AutoDiscSessionsPrefix', self.DEFAULT_AUTO_DISC_SESSIONS_PREFIX)

        self.keepPosition = XMLHelpers.GetXMLAttributeAsBool(element, 'KeepPosition', self.DEFAULT_KEEP_POSITION)
        self.keepSize = XMLHelpers.GetXMLAttributeAsBool(element, 'KeepSize', self.DEFAULT_KEEP_SIZE)
        self.keepDestination = XMLHelpers.GetXMLAttributeAsBool(element, 'KeepDestination', self.DEFAULT_KEEP_DESTINATION)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('AutoDiscSessions', XMLHelpers.BoolToString(self.autoDiscSessions))
        element.setAttribute('AutoDiscSessionsFolder', self.autoDiscSessionsFolder.strip())
        element.setAttribute('AutoDiscSessionsPrefix', self.autoDiscSessionsPrefix.strip())

        element.setAttribute('KeepPosition', XMLHelpers.BoolToString(self.keepPosition))
        element.setAttribute('KeepSize', XMLHelpers.BoolToString(self.keepSize))
        element.setAttribute('KeepDestination', XMLHelpers.BoolToString(self.keepDestination))

        return element

class Preferences(object):
    """ General settings for QtHEP.
    """
    XMLNAME = 'Preferences'        # For this class, and only this class, this is not actually used by fromXML(), toXML()

    def __init__(self):

        self.executables = Executables(self)
        self.logging = Logging(self)
        self.options = Options(self)
        self.newSource = NewSource(self)

        self.filenameTemplates = FilenameTemplates(self)
        self.filenameReplacement = FilenameReplacement(self)

        self.autoCrop = AutoCrop(self)
        self.autoTitle = AutoTitle(self)
        self.autoAudioTracks = AutoAudioTracks(self)
        self.autoSubtitle = AutoSubtitle(self)
        self.autoMixdown = AutoMixdown(self)

        self.presets = Presets(self)
        self.mixdowns = Mixdowns(self)

        self.discSession = DiscSession(self)

    def __str__(self):
        return '{}:\n  {}\n  {}\n  {}\n  {}\n  {}\n  {}\n  {}\n  {}\n  {}\n  {}\n  {}\n  {}\n  {}\n  {}\n'\
            .format(self.XMLNAME, self.executables, self.logging, self.options, self.newSource,
            self.filenameTemplates, self.filenameReplacement, self.autoCrop, self.autoTitle,
            self.autoAudioTracks, self.autoSubtitle, self.autoMixdown, self.presets,
            self.mixdowns, self.discSession)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.executables.clear()
        self.logging.clear()
        self.options.clear()
        self.newSource.clear()

        self.filenameTemplates.clear()
        self.filenameReplacement.clear()

        self.autoCrop.clear()
        self.autoTitle.clear()
        self.autoAudioTracks.clear()
        self.autoSubtitle.clear()
        self.autoMixdown.clear()

        self.presets.clear()
        self.mixdowns.clear()

        self.discSession.clear()

    def fromXML(self, filename):
        """ Initialize the object from an XML element.
        """
        self.clear()

        doc = minidom.parse(filename)
        # The node name changed as part of the QT conversion.
        if (doc.documentElement.nodeName not in ['QtHEP', 'wxHEP']):
            raise RuntimeError(('Can''t read file "{}" because the "QtHEP" '
            'element is missing or misplaced!').format(filename))

        for childNode in doc.documentElement.childNodes:
            if (childNode.localName == Executables.XMLNAME):
                self.executables.fromXML(childNode)
                continue
            if (childNode.localName == Logging.XMLNAME):
                self.logging.fromXML(childNode)
                continue
            if (childNode.localName == Options.XMLNAME):
                self.options.fromXML(childNode)
                continue
            if (childNode.localName == NewSource.XMLNAME):
                self.newSource.fromXML(childNode)
                continue

            if (childNode.localName == FilenameTemplates.XMLNAME):
                self.filenameTemplates.fromXML(childNode)
                continue
            if (childNode.localName == FilenameReplacement.XMLNAME):
                self.filenameReplacement.fromXML(childNode)
                continue

            if (childNode.localName == AutoCrop.XMLNAME):
                self.autoCrop.fromXML(childNode)
                continue
            if (childNode.localName == AutoTitle.XMLNAME):
                self.autoTitle.fromXML(childNode)
                continue
            if (childNode.localName == AutoAudioTracks.XMLNAME):
                self.autoAudioTracks.fromXML(childNode)
                continue
            if (childNode.localName == AutoSubtitle.XMLNAME):
                self.autoSubtitle.fromXML(childNode)
                continue
            if (childNode.localName == AutoMixdown.XMLNAME):
                self.autoMixdown.fromXML(childNode)
                continue

            if (childNode.localName == Presets.XMLNAME):
                self.presets.fromXML(childNode)
                continue
            if (childNode.localName == Mixdowns.XMLNAME):
                self.mixdowns.fromXML(childNode)
                continue

            if (childNode.localName == DiscSession.XMLNAME):
                self.discSession.fromXML(childNode)

        doc.unlink()

        if (not len(self.filenameTemplates)):
            self.filenameTemplates.setDefaults()
        if (not len(self.presets)):
            self.presets.setDefaults()
        if (not len(self.mixdowns)):
            self.mixdowns.setDefaults()

    def toXML(self, filename):
        """ Write the settings to an XML file.
        """
        dom = minidom.getDOMImplementation()
        doc = dom.createDocument(None, 'QtHEP', None)
        parentElement = doc.documentElement

        self.executables.toXML(doc, parentElement)
        self.logging.toXML(doc, parentElement)
        self.options.toXML(doc, parentElement)
        self.newSource.toXML(doc, parentElement)

        self.filenameTemplates.toXML(doc, parentElement)
        self.filenameReplacement.toXML(doc, parentElement)

        self.autoCrop.toXML(doc, parentElement)
        self.autoTitle.toXML(doc, parentElement)
        self.autoAudioTracks.toXML(doc, parentElement)
        self.autoSubtitle.toXML(doc, parentElement)
        self.autoMixdown.toXML(doc, parentElement)

        self.presets.toXML(doc, parentElement)
        self.mixdowns.toXML(doc, parentElement)

        self.discSession.toXML(doc, parentElement)

        xmlFile = open(filename, 'w')
        doc.writexml(xmlFile, '', '\t', '\n')
        xmlFile.close()

        doc.unlink()

    def buildFilename(self, filenameTemplate, title, presetTag, audioTag,
        episodeNumber, episodeTitle, chapterEpisodeTitle):
        """ Build the file name using the preset values.
        """
        filename = FilenameTemplates.buildFilename(filenameTemplate, title, presetTag,
            audioTag, episodeNumber, episodeTitle, chapterEpisodeTitle)

        if (self.filenameReplacement.replaceFilenameCharacters):
            for char in self.filenameReplacement.filenameCharactersToReplace:
                filename = filename.replace(char, self.filenameReplacement.replacementFilenameCharacter)

        return filename

if __name__ == '__main__':

    print ()

    preferences = Preferences()
    if (os.path.exists('QtHEP.defaults.xml')):
        preferences.fromXML('QtHEP.defaults.xml')
        print ("Defaults file read.")

    print ()

    print (preferences.executables)
    print (preferences.logging)
    print (preferences.options)
    print (preferences.newSource)

    print (preferences.filenameTemplates)
    print (preferences.filenameReplacement)

    print (preferences.autoCrop)
    print (preferences.autoTitle)
    print (preferences.autoAudioTracks)
    print (preferences.autoSubtitle)
    print (preferences.autoMixdown)

    print (preferences.presets)
    print (preferences.mixdowns)

    print (preferences.discSession)

    testTemplates = ['<title>.mkv',
        '<eptitle>.mkv',
        '<cetitle>.mkv',
        '<title> - <eptitle>.mkv',
        '<title><epno> - <eptitle>.mkv',
        '<title> - <cetitle>.mkv',
        '<title> [<preset>][acodec].mkv',
        '<title>? [<preset>][acodec].mkv',
        '<$_><title>.mkv']


    print (FilenameTemplates.hasTitleKey('<title>.mkv'))
    print (FilenameTemplates.hasTitleKey('<eptitle>.mkv'))

    print ()
    print ()

    for testTemplate in testTemplates:
        print (FilenameTemplates.buildFilename(testTemplate, 'Buffy the Vampire Slayer 1', 'Film', 'DPL2,AC3', '12', 'Prophecy Girl', 'chapter'))

    print ()
    print ()

    for testTemplate in testTemplates:
        print (preferences.buildFilename(testTemplate, 'Buffy the Vampire Slayer 1', 'Film', 'DPL2,AC3', '12', 'Prophecy Girl', 'chapter'))

    print ()
    print ()

    preferences.filenameReplacement.replaceFilenameCharacters = True
    for testTemplate in testTemplates:
        print (preferences.buildFilename(testTemplate, 'Buffy the Vampire Slayer 1', 'Film', 'DPL2,AC3', '12', 'Prophecy Girl', 'chapter'))

    preferences.toXML('TestFiles/QtHEP.defaults.xml')
