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

# =============================================================================
# This is a helper class for QTextBrowser.  We can't use QTextBrowser.insertHtml()
# because it insists on re-formating the html and stripping out some of the css
# formatting every time it's called.  This makes indenting text in the browser
# impossible.  This problem can be overcome using QTextBroser.setHtml() but that
# means overwritting all of the contents of the widget every time something is
# changed.  So, this class will accumulate the html for the widget and update
# it all, every time it's changed.
# =============================================================================

class ResultsHtml(object):
    """ Accumulate html for the "results" QTextBrowser.  Update the associated
        QTextBrowser widget whenever the html is changed/updated.
    """

    PREFIX_HTML = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
.c0 {color:red; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;}
.c1 {color:blue; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;}
.c2 {color:green; margin-top:0px; margin-bottom:0px; margin-left:20px; margin-right:0px; -qt-block-indent:0; text-indent:0px;}
.c3 {color:black; margin-top:0px; margin-bottom:0px; margin-left:40px; margin-right:0px; -qt-block-indent:0; text-indent:0px;}
</style></head><body style=" font-family:'Noto Sans'; font-size:9pt; font-weight:400; font-style:normal;">"""

    SUFFIX_HTML = '</body></html>'

    def __init__(self, parent, textBrowser):
        super().__init__()

        self.__parent = parent
        self.__textBrowser = textBrowser
        self.__html = ''

    @property
    def parent(self):
        return self.__parent

    def appendHtml(self, html):
        self.__html += html
        self.__update()

    def appendParagraph(self, text, cssClass=None, log=None):
        if (log):
            log.writeline(text)

        if (cssClass):
            self.__html += '<p class="{}">{}</p>'.format(cssClass, text)
        else:
            self.__html += '<p>{}</p>'.format(text)

        self.__update()

    def clear(self):
        self.__html = ''
        self.__update()

    def __update(self):
        self.__textBrowser.setHtml(self.PREFIX_HTML+self.__html+self.SUFFIX_HTML)
        self.__textBrowser.repaint()
