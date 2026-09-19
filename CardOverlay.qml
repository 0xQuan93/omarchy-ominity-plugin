import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.Commons
import qs.Ui as Ui

PanelWindow {
    id: root
    property bool opened: false
    property real reveal: 0
    property real arrival: 1
    property var reading: null
    property var guide: ({})
    property string day: ""
    property string cardImage: ""
    property string backImage: ""
    property string summary: ""
    property string summaryError: ""
    property string errorText: ""
    property bool summaryBusy: false
    property bool adapterAvailable: false
    property bool drawBusy: false
    property bool widgetEnabled: false
    property real flipProgress: 0
    property string page: "reading"
    readonly property var card: reading && reading.card ? reading.card : ({})
    readonly property string orientation: reading && reading.reversed ? "REVERSED" : "UPRIGHT"

    signal closeRequested()
    signal redrawRequested()
    signal summaryRequested()
    signal widgetRequested()

    function resetForDraw() {
        flipAnimation.stop()
        flipProgress = 0
        page = "reading"
        detailScroll.contentY = 0
    }
    function turn() {
        if (!reading || flipAnimation.running) return
        flipAnimation.stop()
        flipAnimation.to = flipProgress < 0.5 ? 1 : 0
        flipAnimation.start()
    }
    onPageChanged: detailScroll.contentY = 0

    visible: false
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "oxquan-ominity-reading"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand

    NumberAnimation {
        id: flipAnimation
        target: root; property: "flipProgress"; duration: 560
        easing.type: Easing.InOutCubic
    }

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.82 * root.reveal)
        MouseArea { anchors.fill: parent; onClicked: root.closeRequested() }
    }

    FocusScope {
        anchors.fill: parent
        focus: root.opened
        Keys.onEscapePressed: root.closeRequested()
        Keys.onSpacePressed: root.turn()

        Item {
            id: cardMount
            height: Math.min(parent.height - 64, 720)
            width: height * 280 / 480
            anchors.centerIn: parent
            anchors.verticalCenterOffset: (1 - root.reveal) * 82
            opacity: root.reveal
            scale: 0.92 + 0.08 * root.reveal
            transform: Scale {
                origin.x: cardMount.width / 2
                origin.y: cardMount.height / 2
                xScale: Math.max(0.01, Math.abs(1 - 2 * root.flipProgress))
            }

            Item {
                anchors.fill: parent
                visible: root.flipProgress <= 0.5
                Image {
                    anchors.fill: parent
                    source: root.backImage
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    asynchronous: true
                    opacity: root.reading ? Math.max(0, Math.min(1, (0.72 - root.arrival) * 4)) : 1
                }
                Image {
                    anchors.fill: parent
                    source: root.cardImage
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    asynchronous: true
                    opacity: root.reading ? Math.max(0, Math.min(1, (root.arrival - 0.38) * 2.8)) : 0
                    rotation: root.reading && root.reading.reversed ? 180 : 0
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.turn()
                }
            }

            Item {
                anchors.fill: parent
                visible: root.flipProgress > 0.5
                Rectangle {
                    anchors.fill: parent
                    radius: 7
                    color: Color.background
                    border.color: Color.accent
                    border.width: 2
                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 9
                        radius: 3
                        color: "transparent"
                        border.color: Qt.alpha(Color.accent, 0.55)
                        border.width: 1
                    }
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.verticalCenterOffset: 115
                    text: root.card.numeral || "✦"
                    visible: root.page === "reading"
                    color: Color.accent
                    opacity: 0.09
                    font.family: "Liberation Serif"
                    font.pixelSize: Math.min(260, cardMount.width * 0.57)
                }

                Column {
                    id: reverse
                    anchors.fill: parent
                    anchors.margins: Math.max(21, parent.width * 0.07)
                    spacing: 10

                    Row {
                        width: parent.width
                        Text {
                            width: parent.width - closeButton.width
                            text: "✦  O M I N I T Y    /    " + root.day
                            color: Color.accent
                            font.family: Style.font.family
                            font.pixelSize: Style.font.caption
                            verticalAlignment: Text.AlignVCenter
                            height: closeButton.height
                        }
                        Ui.Button {
                            id: closeButton
                            text: "×"
                            focusable: true
                            horizontalPadding: 7
                            verticalPadding: 2
                            onClicked: root.closeRequested()
                        }
                    }
                    Text {
                        width: parent.width
                        text: root.card.title || "The reading"
                        color: Color.foreground
                        font.family: "Liberation Serif"
                        font.pixelSize: Math.min(33, cardMount.width / 12)
                        wrapMode: Text.Wrap
                        maximumLineCount: 2
                    }
                    Text {
                        width: parent.width
                        text: (root.card.arcana === "major" ? "MAJOR ARCANA" : String(root.card.suit || "").toUpperCase()) + "   /   " + (root.card.numeral || "") + "   /   " + root.orientation
                        color: Color.accent
                        font.family: Style.font.family
                        font.pixelSize: Style.font.caption
                        wrapMode: Text.Wrap
                    }
                    Rectangle { width: parent.width; height: 1; color: Qt.alpha(Color.accent, 0.66) }
                    Row {
                        spacing: 6
                        Ui.Button { text: "Meaning"; selected: root.page === "reading"; focusable: true; fontSize: Style.font.bodySmall; horizontalPadding: 8; onClicked: root.page = "reading" }
                        Ui.Button { text: "Deeper"; selected: root.page === "explore"; focusable: true; fontSize: Style.font.bodySmall; horizontalPadding: 8; onClicked: root.page = "explore" }
                        Ui.Button { text: "Tarot guide"; selected: root.page === "guide"; focusable: true; fontSize: Style.font.bodySmall; horizontalPadding: 8; onClicked: root.page = "guide" }
                    }

                    Flickable {
                        id: detailScroll
                        width: parent.width
                        height: Math.max(70, parent.height - y - actions.height - 18)
                        clip: true
                        contentWidth: width
                        contentHeight: details.implicitHeight
                        boundsBehavior: Flickable.StopAtBounds
                        Column {
                            id: details
                            width: detailScroll.width
                            spacing: 12
                            Text {
                                width: parent.width
                                visible: root.page === "reading"
                                text: root.reading ? (root.reading.reversed ? root.card.reversed : root.card.upright) : "Your card is arriving."
                                color: Color.foreground
                                font.family: "Liberation Serif"
                                font.pixelSize: 22
                                wrapMode: Text.Wrap
                                lineHeight: 1.08
                            }
                            Text {
                                width: parent.width
                                visible: root.page === "reading"
                                text: root.card.interpretation || ""
                                color: Color.foreground
                                font.family: Style.font.family
                                font.pixelSize: Style.font.body
                                wrapMode: Text.Wrap
                                lineHeight: 1.23
                            }
                            Text {
                                width: parent.width
                                visible: root.page === "reading"
                                text: "REFLECT   " + (root.card.reflection || "")
                                color: Color.accent
                                font.family: "Liberation Serif"
                                font.italic: true
                                font.pixelSize: 19
                                wrapMode: Text.Wrap
                            }
                            Text {
                                width: parent.width
                                visible: root.page === "reading" && root.summary !== ""
                                text: "ZEPHYR  /  " + root.summary
                                color: Color.accent
                                font.family: Style.font.family
                                font.pixelSize: Style.font.body
                                wrapMode: Text.Wrap
                                lineHeight: 1.2
                            }
                            Text {
                                width: parent.width
                                visible: root.page === "explore"
                                text: root.card.path || (root.card.element ? root.card.element + "  /  " + root.card.suit : "The deeper pattern")
                                color: Color.accent
                                font.family: "Liberation Serif"
                                font.pixelSize: 22
                                wrapMode: Text.Wrap
                            }
                            Text {
                                width: parent.width
                                visible: root.page === "explore"
                                text: "UPRIGHT  /  " + (root.card.upright || "") + "\n\nREVERSED  /  " + (root.card.reversed || "") + "\n\n" + (root.card.interpretation || "")
                                color: Color.foreground
                                font.family: Style.font.family
                                font.pixelSize: Style.font.body
                                wrapMode: Text.Wrap
                                lineHeight: 1.22
                            }
                            Text {
                                width: parent.width
                                visible: root.page === "explore"
                                text: "SYMBOLS  /  " + (root.card.symbols || []).join(" · ") + "\n\nKEYWORDS  /  " + (root.card.keywords || []).join(" · ")
                                color: Color.accent
                                font.family: Style.font.family
                                font.pixelSize: Style.font.bodySmall
                                wrapMode: Text.Wrap
                                lineHeight: 1.28
                            }
                            Text {
                                width: parent.width
                                visible: root.page === "guide"
                                text: (root.guide.introduction || "Tarot is a picture language for reflection.") + "\n\n" + ((root.guide.structure || {}).major_arcana || "22 Major Arcana") + "\n\n" + ((root.guide.structure || {}).minor_arcana || "56 Minor Arcana") + "\n\n" + ((root.guide.structure || {}).ranks || "")
                                color: Color.foreground
                                font.family: Style.font.family
                                font.pixelSize: Style.font.body
                                wrapMode: Text.Wrap
                                lineHeight: 1.22
                            }
                            Text {
                                width: parent.width
                                visible: root.page === "guide"
                                text: "WANDS  /  FIRE  /  WILL\nCUPS  /  WATER  /  FEELING\nSWORDS  /  AIR  /  THOUGHT\nPENTACLES  /  EARTH  /  RESOURCES"
                                color: Color.accent
                                font.family: Style.font.family
                                font.pixelSize: Style.font.bodySmall
                                wrapMode: Text.Wrap
                                lineHeight: 1.3
                            }
                            Text {
                                width: parent.width
                                visible: root.page === "guide"
                                text: "REVERSALS  /  " + (root.guide.reversals || "") + "\n\nDAILY RITUAL  /  " + (root.guide.daily_reflection || "") + "\n\n" + (root.guide.influence || "")
                                color: Color.foreground
                                font.family: Style.font.family
                                font.pixelSize: Style.font.body
                                wrapMode: Text.Wrap
                                lineHeight: 1.22
                            }
                            Text {
                                width: parent.width
                                visible: root.errorText !== "" || root.summaryError !== ""
                                text: root.errorText || root.summaryError
                                color: Color.urgent
                                font.family: Style.font.family
                                font.pixelSize: Style.font.bodySmall
                                wrapMode: Text.Wrap
                            }
                        }
                    }

                    Row {
                        id: actions
                        spacing: 6
                        Ui.Button { text: "↶ Art"; focusable: true; fontSize: Style.font.bodySmall; horizontalPadding: 7; onClicked: root.turn() }
                        Ui.Button { text: "Draw again"; focusable: true; fontSize: Style.font.bodySmall; horizontalPadding: 7; enabled: !root.drawBusy; onClicked: root.redrawRequested() }
                        Ui.Button { visible: root.adapterAvailable; text: root.summaryBusy ? "Reading…" : "Ask Zephyr"; focusable: true; fontSize: Style.font.bodySmall; horizontalPadding: 7; enabled: !root.summaryBusy; onClicked: root.summaryRequested() }
                    }
                }
            }
        }
    }
}
