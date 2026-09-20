import QtQuick
import Quickshell
import qs.Commons
import qs.Ui as Ui

Item {
    id: root
    property bool opened: false
    property bool busy: false
    property var reading: null
    property var journal: ({})
    property string errorText: ""
    property string fallbackDirectory: ""
    readonly property var card: reading && reading.card ? reading.card : ({})
    readonly property var experience: reading && reading.experience ? reading.experience : ({})
    readonly property string imagePath: reading && reading.artworkPath ? reading.artworkPath : (card.art && fallbackDirectory ? fallbackDirectory + "/" + card.art : "")
    signal closeRequested()

    visible: opened
    z: 8

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.82)
        MouseArea { anchors.fill: parent; onClicked: root.closeRequested() }
    }

    Ui.BorderSurface {
        id: panel
        width: Math.min(parent.width - 48, 850)
        height: Math.min(parent.height - 48, 700)
        anchors.centerIn: parent
        radius: Style.cornerRadius
        color: Color.popups.background
        borderSpec: Border.localOrSurfaceSpec("popups", "border", Color.popups.border, Color.popups.border, 1)
        MouseArea { anchors.fill: parent }

        Column {
            anchors.fill: parent
            anchors.margins: 22
            spacing: 14

            Row {
                width: parent.width
                Column {
                    width: parent.width - closeButton.width
                    spacing: 3
                    Text { text: "✦  O M I N I T Y   /   DAILY OM"; color: Color.accent; font.family: "Noto Sans"; font.pixelSize: 11; font.letterSpacing: 1 }
                    Text { text: root.reading ? (root.reading.day + "  ·  " + (root.reading.reversed ? "REVERSED" : "UPRIGHT")) : "Opening the archive…"; color: Color.foreground; font.family: "Noto Sans"; font.pixelSize: 13 }
                }
                Ui.Button { id: closeButton; text: "×"; focusable: true; onClicked: root.closeRequested() }
            }
            Rectangle { width: parent.width; height: 1; color: Qt.alpha(Color.accent, 0.55) }
            Text { visible: root.busy || root.errorText !== ""; width: parent.width; text: root.errorText || "Opening the saved reading…"; color: root.errorText ? Color.urgent : Color.accent; font.family: "Noto Sans"; font.pixelSize: 14; wrapMode: Text.Wrap }

            Row {
                visible: !!root.reading
                width: parent.width
                height: parent.height - y
                spacing: 20

                Item {
                    id: artPane
                    width: Math.min(parent.width * 0.43, 300)
                    height: parent.height
                    Image {
                        anchors.fill: parent
                        source: root.imagePath ? Util.fileUrl(root.imagePath) : ""
                        fillMode: Image.PreserveAspectFit
                        rotation: root.reading && root.reading.reversed ? 180 : 0
                        asynchronous: true
                        visible: source !== ""
                    }
                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 24
                        visible: !root.imagePath
                        text: "Artwork is unavailable for this reading. Its saved words remain."
                        color: Color.muted
                        font.family: "Noto Serif"
                        font.pixelSize: 18
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                    }
                }

                Flickable {
                    id: scroll
                    width: parent.width - artPane.width - 20
                    height: parent.height
                    contentWidth: width
                    contentHeight: words.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    Column {
                        id: words
                        width: scroll.width
                        spacing: 13
                        Text { text: root.card.title || "The reading"; width: parent.width; color: Color.foreground; font.family: "Noto Serif"; font.pixelSize: 30; wrapMode: Text.Wrap }
                        Text { text: root.reading ? (root.reading.archiveStatus === "verified-original" ? "ORIGINAL ARTWORK VERIFIED" : "CURRENT DECK RECONSTRUCTION  /  ORIGINAL NOT WITNESSED") : ""; width: parent.width; color: Color.accent; font.family: "Noto Sans"; font.pixelSize: 11; font.letterSpacing: 1; wrapMode: Text.Wrap }
                        Text { text: root.reading ? (root.reading.reversed ? root.card.reversed : root.card.upright) : ""; width: parent.width; color: Color.foreground; font.family: "Noto Serif"; font.pixelSize: 21; wrapMode: Text.Wrap }
                        Text { text: root.card.interpretation || ""; width: parent.width; color: Color.foreground; font.family: "Noto Sans"; font.pixelSize: 14; wrapMode: Text.Wrap; lineHeight: 1.2 }
                        Text { visible: !!(root.experience.facet || {}).text; text: "LENS  /  " + ((root.experience.facet || {}).text || ""); width: parent.width; color: Color.foreground; font.family: "Noto Sans"; font.pixelSize: 14; wrapMode: Text.Wrap }
                        Text { visible: !!(root.experience.symbol || {}).observation; text: "NOTICE  /  " + ((root.experience.symbol || {}).observation || ""); width: parent.width; color: Color.foreground; font.family: "Noto Sans"; font.pixelSize: 14; wrapMode: Text.Wrap }
                        Text { visible: !!(root.experience.thread || {}).text; text: "THE THREAD  /  " + ((root.experience.thread || {}).text || ""); width: parent.width; color: Color.foreground; font.family: "Noto Sans"; font.pixelSize: 14; wrapMode: Text.Wrap }
                        Text { text: "CARRY THIS  /  " + ((root.experience.prompt || {}).text || root.card.reflection || ""); width: parent.width; color: Color.accent; font.family: "Noto Serif"; font.italic: true; font.pixelSize: 18; wrapMode: Text.Wrap }
                        Text { visible: !!root.journal.firstImpression; text: "FIRST IMPRESSION  /  " + (root.journal.firstImpression || ""); width: parent.width; color: Color.foreground; font.family: "Noto Sans"; font.pixelSize: 14; wrapMode: Text.Wrap }
                        Text { visible: !!root.journal.eveningReflection; text: "EVENING REFLECTION  /  " + (root.journal.eveningReflection || ""); width: parent.width; color: Color.foreground; font.family: "Noto Sans"; font.pixelSize: 14; wrapMode: Text.Wrap }
                    }
                }
            }
        }
    }
}
