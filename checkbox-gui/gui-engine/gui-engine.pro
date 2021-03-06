# This file is part of Checkbox
#
# Copyright 2013 Canonical Ltd.
#
# Authors:
# - Andrew Haigh <andrew.haigh@cellsoftware.co.uk>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# gui-engine.pro
#
# Hand-made pro file to create the gui-engine plugin for checkbox-gui

TEMPLATE = lib
CONFIG += qt plugin
QT +=qml dbus xml widgets gui

isEmpty(PREFIX) {
      PREFIX = /usr/local
}

TARGET = gui-engine

HEADERS = gui-engine.h \
    PBTreeNode.h \
    PBTypes.h \
    PBNames.h \
    JobTreeNode.h \
    PBJsonUtils.h

SOURCES = gui-engine.cpp \
    PBTreeNode.cpp \
    JobTreeNode.cpp \
    PBJsonUtils.cpp

DESTDIR = ../lib/checkbox-gui/plugins

target.path = $$PREFIX/lib/checkbox-gui/plugins

INSTALLS += target
