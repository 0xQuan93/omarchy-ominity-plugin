import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.Commons
import qs.Ui as Ui

PanelWindow {
    id: root
    property bool opened: false
    property var stats: ({})
    property var entries: []
    property string errorText: ""
    property string range: "all"
    property var selectedCard: null
    readonly property var cards: stats && stats.perCard ? stats.perCard : []
    readonly property var activeStats: range === "all" ? stats : ((stats.windows || {})[range] || stats)
    readonly property string bodyFont: "Noto Sans"
    readonly property string displayFont: "Noto Serif"

    signal closeRequested()

    function percentage(value) {
        return Math.round(1000 * (Number(value) || 0)) / 10 + "%"
    }
    function cardCount(id) {
        if (range === "all") {
            for (var i = 0; i < cards.length; ++i) if (cards[i].id === id) return cards[i].count || 0
            return 0
        }
        var counts = activeStats.perCard || {}
        if (Array.isArray(counts)) {
            for (var j = 0; j < counts.length; ++j) if (counts[j].id === id) return counts[j].count || 0
        }
        return Number(counts[id]) || 0
    }
    function cardShare(id) {
        var days = Number(activeStats.days) || 0
        return days ? cardCount(id) / days : 0
    }
    function datesFor(id) {
        var dates = []
        for (var i = entries.length - 1; i >= 0; --i) {
            if (entries[i].id === id) dates.push(entries[i].day + (entries[i].reversed ? " · reversed" : " · upright"))
            if (dates.length >= 8) break
        }
        return dates.join("\n")
    }

    visible: false
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "oxquan-ominity-constellation"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.86)
        MouseArea { anchors.fill: parent; onClicked: root.closeRequested() }
    }

    FocusScope {
        anchors.fill: parent
        focus: root.opened
        Keys.onEscapePressed: root.closeRequested()

        Ui.BorderSurface {
            id: surface
            width: Math.min(parent.width - 36, 1120)
            height: Math.min(parent.height - 36, 860)
            anchors.centerIn: parent
            radius: Style.cornerRadius
            color: Color.popups.background
            borderSpec: Border.localOrSurfaceSpec("popups", "border", Color.popups.border, Color.popups.border, 1)

            Column {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 14

                Row {
                    width: parent.width
                    spacing: 12
                    Column {
                        width: parent.width - closeButton.width - 12
                        spacing: 4
                        Text { text: "✦  O M I N I T Y   /   YOUR CONSTELLATION"; color: Color.accent; font.family: root.bodyFont; font.pixelSize: Math.max(11, Style.font.caption) }
                        Text { text: "A history of encounters"; color: Color.foreground; font.family: root.displayFont; font.pixelSize: Math.min(30, surface.width / 26) }
                    }
                    Ui.Button { id: closeButton; text: "×"; focusable: true; onClicked: root.closeRequested() }
                }

                Text {
                    visible: root.errorText !== ""
                    width: parent.width
                    text: root.errorText
                    color: Color.urgent
                    font.family: root.bodyFont
                    font.pixelSize: Math.max(13, Style.font.bodySmall)
                    wrapMode: Text.Wrap
                }

                Row {
                    width: parent.width
                    spacing: 8
                    Repeater {
                        model: [
                            {label: "RITUAL DAYS", value: String(root.stats.days || 0)},
                            {label: "CARDS SEEN", value: String(root.stats.uniqueCards || 0) + " / 78"},
                            {label: "CURRENT STREAK", value: String(((root.stats.streak || {}).current) || 0)},
                            {label: "REDRAWS", value: String(root.stats.redrawCount || 0)}
                        ]
                        delegate: Rectangle {
                            width: (surface.width - 48 - 24) / 4
                            height: 73
                            radius: Style.cornerRadius
                            color: Qt.alpha(Color.foreground, 0.045)
                            border.color: Qt.alpha(Color.accent, 0.28)
                            Column {
                                anchors.fill: parent; anchors.margins: 10; spacing: 3
                                Text { text: modelData.value; color: Color.foreground; font.family: root.displayFont; font.pixelSize: 24 }
                                Text { text: modelData.label; color: Color.accent; font.family: root.bodyFont; font.pixelSize: 10; font.letterSpacing: 1 }
                            }
                        }
                    }
                }

                Row {
                    spacing: 6
                    Text { text: "VIEW"; color: Color.muted; font.family: root.bodyFont; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter }
                    Repeater {
                        model: [{id:"all",label:"Lifetime"},{id:"7",label:"7 days"},{id:"30",label:"30 days"},{id:"90",label:"90 days"}]
                        delegate: Ui.Button {
                            text: modelData.label
                            selected: root.range === modelData.id
                            focusable: true
                            fontFamily: root.bodyFont
                            fontSize: Math.max(12, Style.font.bodySmall)
                            horizontalPadding: 8
                            onClicked: root.range = modelData.id
                        }
                    }
                }

                Row {
                    width: parent.width
                    height: Math.max(230, parent.height - y - footer.height - 22)
                    spacing: 16

                    Rectangle {
                        id: starField
                        width: Math.max(280, parent.width * 0.66)
                        height: parent.height
                        radius: Style.cornerRadius
                        color: Qt.alpha(Color.background, 0.64)
                        border.color: Qt.alpha(Color.accent, 0.28)
                        Column {
                            anchors.fill: parent; anchors.margins: 14; spacing: 8
                            Text { text: "THE 78 CARD SKY"; color: Color.accent; font.family: root.bodyFont; font.pixelSize: 11; font.letterSpacing: 1.5 }
                            GridView {
                                id: cardGrid
                                width: parent.width
                                height: parent.height - 26
                                clip: true
                                model: root.cards
                                cellWidth: Math.max(54, Math.floor(width / Math.max(4, Math.floor(width / 62))))
                                cellHeight: 59
                                boundsBehavior: Flickable.StopAtBounds
                                delegate: Item {
                                    width: cardGrid.cellWidth; height: cardGrid.cellHeight
                                    readonly property int count: root.cardCount(modelData.id)
                                    Rectangle {
                                        width: parent.width - 5; height: parent.height - 5
                                        radius: 5
                                        color: count ? Qt.alpha(Color.accent, Math.min(0.35, 0.10 + count * 0.055)) : Qt.alpha(Color.foreground, 0.035)
                                        border.color: root.selectedCard && root.selectedCard.id === modelData.id ? Color.accent : Qt.alpha(Color.accent, count ? 0.66 : 0.18)
                                        border.width: root.selectedCard && root.selectedCard.id === modelData.id ? 2 : 1
                                        Column {
                                            anchors.centerIn: parent; spacing: 2
                                            Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.arcana === "major" ? (modelData.numeral || "✦") : (modelData.suit || "").slice(0, 1); color: count ? Color.foreground : Color.muted; font.family: root.displayFont; font.pixelSize: 17 }
                                            Text { anchors.horizontalCenter: parent.horizontalCenter; text: count ? String(count) : "·"; color: Color.accent; font.family: root.bodyFont; font.pixelSize: 10 }
                                        }
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.selectedCard = modelData }
                                    }
                                }
                            }
                        }
                    }

                    Column {
                        width: parent.width - starField.width - 16
                        height: parent.height
                        spacing: 10
                        Text { text: root.selectedCard ? root.selectedCard.title : "Select a card"; width: parent.width; color: Color.foreground; font.family: root.displayFont; font.pixelSize: 23; wrapMode: Text.Wrap }
                        Text { text: root.selectedCard ? (String(root.cardCount(root.selectedCard.id)) + " encounters · " + root.percentage(root.cardShare(root.selectedCard.id))) : "Seen cards glow. Unseen cards wait quietly."; width: parent.width; color: Color.accent; font.family: root.bodyFont; font.pixelSize: 13; wrapMode: Text.Wrap }
                        Rectangle { width: parent.width; height: 1; color: Qt.alpha(Color.accent, 0.38) }
                        Text { text: root.selectedCard ? ("LAST SEEN  /  " + (root.selectedCard.lastDay || "never")) : "The pattern grows one day at a time."; width: parent.width; color: Color.foreground; font.family: root.bodyFont; font.pixelSize: 12; wrapMode: Text.Wrap }
                        Text { text: root.selectedCard ? root.datesFor(root.selectedCard.id) : ""; width: parent.width; color: Color.foreground; opacity: 0.75; font.family: root.bodyFont; font.pixelSize: 12; wrapMode: Text.Wrap; lineHeight: 1.24 }
                        Item { width: 1; height: Math.max(0, parent.height - 300) }
                        Text { text: "MAJOR  " + root.percentage((root.activeStats.arcana || {}).major) + "   ·   MINOR  " + root.percentage((root.activeStats.arcana || {}).minor); width: parent.width; color: Color.muted; font.family: root.bodyFont; font.pixelSize: 12; wrapMode: Text.Wrap }
                        Text { text: "UPRIGHT  " + root.percentage((root.activeStats.orientation || {}).upright) + "   ·   REVERSED  " + root.percentage((root.activeStats.orientation || {}).reversed); width: parent.width; color: Color.muted; font.family: root.bodyFont; font.pixelSize: 12; wrapMode: Text.Wrap }
                    }
                }

                Column {
                    id: footer
                    width: parent.width
                    spacing: 4
                    Rectangle { width: parent.width; height: 1; color: Qt.alpha(Color.accent, 0.48) }
                    Text { text: "MACHINE ERAS  /  " + ((root.stats.eras || []).length ? (root.stats.eras || []).map(function(e) { return e.displayLabel + " · " + e.days + " days" }).join("    •    ") : "Your first era begins with a daily Om."); width: parent.width; color: Color.accent; font.family: root.bodyFont; font.pixelSize: 12; elide: Text.ElideRight }
                    Text { text: "Card frequencies describe recorded encounters. They are prompts for reflection, never predictions."; width: parent.width; color: Color.muted; font.family: root.bodyFont; font.pixelSize: 11; wrapMode: Text.Wrap }
                }
            }
        }
    }
}
