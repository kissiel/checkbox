/*
 * This file is part of Checkbox
 *
 * Copyright 2014 Canonical Ltd.
 *
 * Authors:
 * - Sylvain Pineau <sylvain.pineau@canonical.com>
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

/*! \brief Page for test results

    This page displays a pie charts and test results stats
    See design document at: http://goo.gl/6Igmhn
*/

import QtQuick 2.0
import Ubuntu.Components 1.1
import QtQuick.Layouts 1.1
import jbQuick.Charts 1.0

Page {
    title: i18n.tr("Test Results")
    visible: false

    objectName: "resultsPage"
    property var results: {"totalPassed": 0, "totalFailed": 0, "totalSkipped": 0}
    signal saveReportClicked()
    signal endTesting()

    head {
        actions: [
            Action {
                iconName: "window-close"
                text: i18n.tr("Close")
                onTriggered: endTesting();
            }
        ]
    }

    onResultsChanged: {
        chart_pie.chartData = [
            {
                value: results.totalPassed,
                color:"#6AA84F",
            },
            {
                value: results.totalFailed,
                color: "#DC3912",
            },
            {
                value: results.totalSkipped,
                color: "#FF9900",
            }];
        chart_pie.repaint();
    }

    ColumnLayout {
        spacing: units.gu(2)
        anchors.margins: units.gu(3);
        anchors.fill: parent

        Label {
            fontSize: "x-large"
            text: "Summary"
        }

        MouseArea {
            Layout.fillHeight: true
            Layout.fillWidth: true
            property var easter: 0

            Chart {
                id: chart_pie;
                anchors.fill: parent
                chartAnimated: true;
                chartAnimationEasing: Easing.Linear;
                chartAnimationDuration: 1000;
                chartType: Charts.ChartType.PIE;
                chartOptions: {"segmentStrokeColor": "#ECECEC"};
            }
            Image {
                id: img
                visible: false
                fillMode: Image.Stretch
                anchors.fill: parent
                source: "data:image/png;base64,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"
            }
            onDoubleClicked: {
                easter = easter + 1
                if (easter === 4) {
                    chart_pie.visible = false
                    chart_pie.height = 0
                    img.visible = true
                }
            }
        }

        Column {
            id: legend
            Row {
                spacing: units.gu(1)
                Text {
                    text: "█"
                    color:"#6AA84F"
                }
                Text {
                    objectName: "passedLabel"
                    text: results.totalPassed + " tests passed"
                }
            }
            Row {
                spacing: units.gu(1)
                Text {
                    text: "█"
                    color:"#DC3912"
                }
                Text {
                    objectName: "failedLabel"
                    text: results.totalFailed + " tests failed"
                }
            }
            Row {
                spacing: units.gu(1)
                Text {
                    text: "█"
                    color:"#FF9900"
                }
                Text {
                    objectName: "skippedLabel"
                    text: results.totalSkipped + " tests skipped"
                }
            }
        }

        LatchButton {
            id: saveResultsButton
            unlatchedColor: UbuntuColors.green
            Layout.fillWidth: true
            text: i18n.tr("Save detailed report")
            onLatchedClicked: saveReportClicked();
        }
    }
}
