/*
 * This file is part of Checkbox
 *
 * Copyright 2014 Canonical Ltd.
 *
 * Authors:
 * - Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
 * - Maciej Kisielewski <maciej.kisielewski@canonical.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import QtQuick 2.0
import Ubuntu.Components 1.1

Page {
    id: automatedTestPage

    property var testName
    property var testDescription
    signal startActivity();
    signal stopActivity();

    title: i18n.tr("Automated test")

    visible: false

    Label {
        id: testNameLabel

        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
        }

        text: testName
        font.pixelSize: units.gu(4)
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignLeft
        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
    }

    Label {
        id: testDescrptionLabel

        anchors {
            top: testNameLabel.bottom
            left: parent.left
            right: parent.right
            topMargin: units.gu(4)
        }

        text: testDescription
        font.pixelSize: units.gu(3)
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
    }

    ActivityIndicator {
        id: activity
        height: units.gu(10)
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            margins: units.gu(2)
        }
    }
    onStartActivity: {
        activity.running = true;
    }
    onStopActivity: {
        activity.running = false;
    }
    Component.onCompleted: {
        startActivity();
    }
}
