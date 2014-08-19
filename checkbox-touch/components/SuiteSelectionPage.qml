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
import Ubuntu.Components.ListItems 0.1 as ListItem

Page {
    id: suiteSelectionPage

    property var checkBoxStack
    signal selectionChanged(int index, bool checked)

    title: i18n.tr("Suite Selection")

    visible: false

    head {
            actions: [
                Action {
                    iconName: "select"
                    text: i18n.tr("Select All")
                    onTriggered: {
                        console.log("Select all triggered")
                    }
                },
                Action {
                    iconName: "media-playback-start"
                    text: i18n.tr("Start")
                    onTriggered: {
                        console.log("Start triggered")
                    }
                }
            ]
        }
    ListView {
        spacing: 8
        anchors.fill: parent
        anchors.margins: units.gu(2)

        model: 15 //TODO: replace with list querried from plainbox

        delegate: categorySelection

    }
    Component {
        id: categorySelection
        Item {
            width: parent.width

            height: units.gu(4)
            Text {
                font.pixelSize: units.gu(3)
                text: "Category " + index
            }
            CheckBox {
                id: checkbox
                anchors.right: parent.right
                onClicked:{
                    selectionChanged(index, checkbox.checked)
                }
            }

        }
    }
    onSelectionChanged:{
        console.log("Selection changed. Item " + index + " is now" + (checked? " checked": " unchecked") + ".")
    }
    Button {
        id: startTestButton

        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            margins: units.gu(2)
        }

        color: UbuntuColors.green
        text: i18n.tr("Start Testing")
        onClicked: main.suiteSelectionDone();
    }

}
