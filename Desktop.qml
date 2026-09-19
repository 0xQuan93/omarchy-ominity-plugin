import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import qs.Ui as Ui

Item {
    id: root
    readonly property string home: Quickshell.env("HOME")
    readonly property string configHome: Quickshell.env("XDG_CONFIG_HOME") || home + "/.config"
    readonly property string pluginDir: configHome + "/omarchy/plugins/oxquan.ominity"
    readonly property string adapter: configHome + "/ominity/summary"
    property var reading: null
    property string day: ""
    property bool widgetEnabled: false
    property bool overlayOpen: false
    property bool overlayPresent: false
    property real reveal: 0
    property real cardArrival: 1
    property string page: "reading"
    property string busyAction: ""
    property string queuedAction: ""
    property string errorText: ""
    property string summaryText: ""
    property string summaryError: ""
    property bool adapterAvailable: false
    property var guide: ({})
    readonly property var card: reading && reading.card ? reading.card : ({})
    readonly property string orientation: reading && reading.reversed ? "REVERSED" : "UPRIGHT"
    readonly property string cardImage: card.art ? Util.fileUrl(pluginDir + "/" + card.art) : ""
    onPageChanged: if (scroll) scroll.contentY = 0

    function doAction(action) {
        if (stateProc.running) { queuedAction = action; return }
        busyAction = action
        errorText = ""
        stateProc.command = ["/usr/bin/python3", "-B", pluginDir + "/ominity.py", action]
        stateProc.running = true
    }

    function acceptState(raw) {
        try {
            var next = JSON.parse(raw)
            if (!next.ok) throw new Error(next.error || "Could not read the deck")
            var oldStamp = reading ? reading.drawnAt : ""
            day = next.day || ""
            reading = next.reading
            widgetEnabled = next.widget === true
            if (reading && oldStamp !== reading.drawnAt) {
                summaryText = ""
                summaryError = ""
                cardArrival = 0
                arrivalAnimation.restart()
            }
        } catch (e) { errorText = String(e) }
    }

    function openReading() {
        page = "reading"
        overlayOpen = true
        overlayPresent = true
        revealAnimation.stop()
        revealAnimation.to = 1
        revealAnimation.start()
        doAction("today")
    }

    function closeReading() {
        overlayOpen = false
        revealAnimation.stop()
        revealAnimation.to = 0
        revealAnimation.start()
    }

    function toggleReading() { if (overlayOpen) closeReading(); else openReading() }
    function toggleWidget() { doAction("widget-toggle") }
    function redraw() { page = "reading"; doAction("redraw") }
    function summarize() {
        if (!reading || summaryProc.running || !adapterAvailable) return
        summaryError = ""
        summaryText = ""
        summaryProc.command = [adapter, reading.drawnAt]
        summaryProc.running = true
    }

    Process {
        id: stateProc
        stdout: StdioCollector { onStreamFinished: root.acceptState(text) }
        onExited: function(code) {
            root.busyAction = ""
            if (code !== 0 && !root.errorText) root.errorText = "The local deck could not be read."
            if (root.queuedAction) {
                var next = root.queuedAction
                root.queuedAction = ""
                root.doAction(next)
            }
        }
    }
    Process {
        id: summaryProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    if (result.ok && typeof result.summary === "string" && root.reading && result.drawnAt === root.reading.drawnAt) root.summaryText = result.summary
                    else root.summaryError = result.error || "Zephyr could not create a reading."
                } catch (e) { root.summaryError = "Zephyr returned an unreadable summary." }
            }
        }
        onExited: function(code) {
            if (code !== 0 && !root.summaryError) root.summaryError = "Zephyr is unavailable right now."
        }
    }
    FileView {
        path: root.adapter
        watchChanges: true
        onLoaded: root.adapterAvailable = true
        onFileChanged: reload()
    }
    FileView {
        path: root.pluginDir + "/deck/guide.json"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try { root.guide = JSON.parse(text()) }
            catch (e) { root.guide = ({}) }
        }
    }
    NumberAnimation {
        id: revealAnimation
        target: root; property: "reveal"; duration: 360; easing.type: Easing.OutCubic
        onStopped: if (!root.overlayOpen && root.reveal <= 0.001) root.overlayPresent = false
    }
    NumberAnimation {
        id: arrivalAnimation
        target: root; property: "cardArrival"; from: 0; to: 1
        duration: 680; easing.type: Easing.OutBack; easing.overshoot: 1.06
    }
    IpcHandler {
        target: "ominity"
        function open(): void { root.openReading() }
        function close(): void { root.closeReading() }
        function toggle(): void { root.toggleReading() }
        function draw(): void { root.openReading() }
        function redraw(): void { root.redraw() }
        function widget(): void { root.toggleWidget() }
        function status(): string { return JSON.stringify({open: root.overlayOpen, widget: root.widgetEnabled, day: root.day, card: root.card.id || ""}) }
    }
    Timer {
        interval: 60000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: if (!root.overlayOpen) root.doAction("state")
    }

    PanelWindow {
        id: desktopWidget
        screen: Quickshell.screens[0]
        visible: root.widgetEnabled && !root.overlayPresent
        anchors { top: true; left: true }
        margins { left: 34; top: Math.max(82, screen.height * 0.39) }
        implicitWidth: Math.min(318, screen.width - 68)
        implicitHeight: 178
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "oxquan-ominity-widget"
        WlrLayershell.layer: WlrLayer.Bottom
        Ui.BorderSurface {
            anchors.fill: parent
            radius: Style.cornerRadius
            color: Color.popups.background
            borderSpec: Border.localOrSurfaceSpec("popups", "border", Color.popups.border, Color.popups.border, 1)
            Rectangle { width: 3; height: parent.height - 30; x: 15; y: 15; color: Color.accent }
            Column {
                anchors.fill: parent; anchors.margins: 22; anchors.leftMargin: 31; spacing: 9
                Text { text: "✦  O M I N I T Y   /   " + (root.day || "TODAY"); color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.caption }
                Text { width: parent.width; text: root.reading ? root.card.title : "A card waits for you"; color: Color.popups.text; font.family: "Liberation Serif"; font.pixelSize: 27; elide: Text.ElideRight }
                Text { width: parent.width; text: root.reading ? root.orientation + "  ·  " + (root.card.keywords || []).slice(0, 2).join(" / ") : "A small ritual for the day ahead."; color: Color.popups.text; opacity: 0.7; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall; elide: Text.ElideRight }
                Text { text: root.reading ? "OPEN THE READING  ↗" : "PULL TODAY'S CARD  ↗"; color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall }
            }
            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.openReading() }
        }
    }

    PanelWindow {
        id: readingWindow
        screen: Quickshell.screens[0]
        visible: root.overlayPresent
        anchors { top: true; bottom: true; left: true; right: true }
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "oxquan-ominity-reading"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
        Rectangle {
            anchors.fill: parent
            color: Qt.rgba(0, 0, 0, 0.78 * root.reveal)
            MouseArea { anchors.fill: parent; onClicked: root.closeReading() }
        }
        FocusScope {
            anchors.fill: parent; focus: root.overlayOpen
            Keys.onEscapePressed: root.closeReading()
            Ui.BorderSurface {
                id: stage
                width: Math.min(parent.width - 52, 1030)
                height: Math.min(parent.height - 62, 630)
                anchors.centerIn: parent
                anchors.verticalCenterOffset: (1 - root.reveal) * 44
                opacity: root.reveal
                radius: Math.max(Style.cornerRadius, 12)
                color: Qt.alpha(Color.popups.background, 0.97)
                borderSpec: Border.localOrSurfaceSpec("popups", "border", Color.popups.border, Color.popups.border, 1)
                Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; height: 3; color: Color.accent }
                Column {
                    anchors.fill: parent; anchors.margins: Math.min(30, parent.width * 0.04); spacing: 18
                    Row {
                        width: parent.width; spacing: 12
                        Column {
                            width: parent.width - controls.width - 15; spacing: 5
                            Text { text: "✦   O M I N I T Y     /     DAILY DIVINATION"; color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall }
                            Text { text: root.page === "guide" ? "The practice" : root.page === "explore" ? "Inside the card" : "A moment to look closer"; color: Color.popups.text; font.family: "Liberation Serif"; font.pixelSize: Math.min(33, stage.width / 26) }
                        }
                        Row {
                            id: controls; spacing: 8
                            Ui.Button { text: "Reading"; selected: root.page === "reading"; focusable: true; onClicked: root.page = "reading" }
                            Ui.Button { text: "Explore"; selected: root.page === "explore"; focusable: true; onClicked: root.page = "explore" }
                            Ui.Button { text: "Guide"; selected: root.page === "guide"; focusable: true; onClicked: root.page = "guide" }
                            Ui.Button { text: "Close"; focusable: true; onClicked: root.closeReading() }
                        }
                    }
                    Rectangle { width: parent.width; height: 1; color: Color.popups.border; opacity: 0.55 }
                    Flickable {
                        id: scroll
                        width: parent.width; height: parent.height - y
                        clip: true; contentWidth: width; contentHeight: body.implicitHeight
                        boundsBehavior: Flickable.StopAtBounds
                        Column {
                            id: body; width: scroll.width; spacing: 20
                            Flow {
                                width: parent.width; spacing: 30
                                Item {
                                    id: artStage
                                    width: Math.min(284, body.width)
                                    height: 455
                                    Image {
                                        width: Math.min(parent.width, 282); height: 440
                                        source: Util.fileUrl(root.pluginDir + "/assets/card-back.svg")
                                        fillMode: Image.PreserveAspectFit
                                        smooth: true; asynchronous: true
                                        x: (parent.width - width) / 2 + (1 - root.cardArrival) * 110
                                        y: (parent.height - height) / 2 + (1 - root.cardArrival) * 34
                                        rotation: (1 - root.cardArrival) * -8
                                        opacity: !root.reading ? 1 : Math.max(0, Math.min(1, (0.68 - root.cardArrival) * 4))
                                    }
                                    Image {
                                        id: art
                                        width: Math.min(parent.width, 282); height: 440
                                        source: root.cardImage
                                        fillMode: Image.PreserveAspectFit
                                        smooth: true; asynchronous: true
                                        opacity: root.reading ? Math.max(0, Math.min(1, (root.cardArrival - 0.35) * 2.8)) : 0
                                        x: (parent.width - width) / 2 + (1 - root.cardArrival) * 110
                                        y: (parent.height - height) / 2 + (1 - root.cardArrival) * 34
                                        rotation: (1 - root.cardArrival) * 8 + (root.reading && root.reading.reversed ? 180 : 0)
                                    }
                                    Rectangle {
                                        anchors.fill: art; color: "transparent"; border.color: Color.accent
                                        border.width: 1; opacity: 0.35 * root.cardArrival
                                    }
                                }
                                Column {
                                    width: body.width > 700 ? body.width - artStage.width - 30 : body.width
                                    spacing: 15
                                    Text { text: root.reading ? root.day + "    /    " + root.orientation : "YOUR DAILY CARD"; color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall }
                                    Text { width: parent.width; text: root.reading ? root.card.title : "The deck is gathering…"; color: Color.popups.text; font.family: "Liberation Serif"; font.pixelSize: 39; wrapMode: Text.Wrap }
                                    Text { width: parent.width; text: root.reading ? ((root.card.arcana === "major" ? "MAJOR ARCANA" : String(root.card.suit || "").toUpperCase()) + "  ·  " + (root.card.numeral || root.card.number || "")) : ""; color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall }
                                    Rectangle { width: parent.width; height: 1; color: Color.popups.border; opacity: 0.5 }
                                    Text { width: parent.width; text: root.page === "guide" ? "READING THE CARDS" : root.page === "explore" ? "ARCHETYPE  /  SYMBOL  /  CHOICE" : "THE INVITATION"; color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.caption }
                                    Text { width: parent.width; text: root.page === "guide" ? (root.guide.introduction || "Tarot is a picture language for reflection.") : root.page === "explore" ? (root.card.path || (root.card.element ? root.card.element + " / " + root.card.suit : "A closer look")) : (root.reading ? (root.reading.reversed ? root.card.reversed : root.card.upright) : "Take one quiet breath. Your card will arrive here."); color: Color.popups.text; font.family: "Liberation Serif"; font.pixelSize: 22; wrapMode: Text.Wrap; lineHeight: 1.12 }
                                    Text { width: parent.width; visible: root.page === "reading" && !!root.reading; text: root.card.interpretation || ""; color: Color.popups.text; opacity: 0.83; font.family: Style.font.family; font.pixelSize: Style.font.body; wrapMode: Text.Wrap; lineHeight: 1.28 }
                                    Text { width: parent.width; visible: root.page === "reading" && !!root.reading; text: "LOOK FOR   " + (root.card.symbols || []).join("   ·   "); color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall; wrapMode: Text.Wrap }
                                    Text { width: parent.width; visible: root.page === "reading" && !!root.reading; text: "REFLECT   " + (root.card.reflection || ""); color: Color.popups.text; font.family: "Liberation Serif"; font.italic: true; font.pixelSize: 20; wrapMode: Text.Wrap }
                                    Text { width: parent.width; visible: root.page === "explore" && !!root.reading; text: "UPRIGHT  /  " + (root.card.upright || "") + "\n\nREVERSED  /  " + (root.card.reversed || ""); color: Color.popups.text; font.family: Style.font.family; font.pixelSize: Style.font.body; wrapMode: Text.Wrap; lineHeight: 1.3 }
                                    Text { width: parent.width; visible: root.page === "explore" && !!root.reading; text: root.card.interpretation || ""; color: Color.popups.text; font.family: "Liberation Serif"; font.pixelSize: 20; wrapMode: Text.Wrap; lineHeight: 1.15 }
                                    Text { width: parent.width; visible: root.page === "explore" && !!root.reading; text: "SYMBOLS  /  " + (root.card.symbols || []).join(" · ") + "\n\nKEYWORDS  /  " + (root.card.keywords || []).join(" · ") + "\n\nQUESTION  /  " + (root.card.reflection || ""); color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.body; wrapMode: Text.Wrap; lineHeight: 1.3 }
                                    Text { width: parent.width; visible: root.page === "guide"; text: "THE DECK  /  " + ((root.guide.structure || {}).major_arcana || "22 Major Arcana") + "\n\n" + ((root.guide.structure || {}).minor_arcana || "56 Minor Arcana") + "\n\n" + ((root.guide.structure || {}).ranks || ""); color: Color.popups.text; font.family: Style.font.family; font.pixelSize: Style.font.body; wrapMode: Text.Wrap; lineHeight: 1.3 }
                                    Text { width: parent.width; visible: root.page === "guide"; text: "THE SUITS\nWands  /  fire  /  creative will\nCups  /  water  /  feeling and connection\nSwords  /  air  /  thought and discernment\nPentacles  /  earth  /  body, work, resources"; color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.body; wrapMode: Text.Wrap; lineHeight: 1.3 }
                                    Text { width: parent.width; visible: root.page === "guide"; text: "REVERSALS  /  " + (root.guide.reversals || "A reversal can suggest an inward or delayed expression.") + "\n\nTHE DAILY RITUAL  /  " + (root.guide.daily_reflection || "Draw once and return later."); color: Color.popups.text; font.family: Style.font.family; font.pixelSize: Style.font.body; wrapMode: Text.Wrap; lineHeight: 1.3 }
                                    Text { width: parent.width; visible: root.page === "guide"; text: "Inspired by the classic Rider–Waite–Smith structure and by Starman Tarot's interest in transformation and creative possibility. Ominity's art and readings are original; it is unaffiliated with the Starman publishers or creators."; color: Color.popups.text; opacity: 0.65; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall; wrapMode: Text.Wrap }
                                    Text { width: parent.width; visible: root.summaryText !== ""; text: "ZEPHYR'S READING  /  " + root.summaryText; color: Color.accent; font.family: Style.font.family; font.pixelSize: Style.font.body; wrapMode: Text.Wrap; lineHeight: 1.25 }
                                    Text { width: parent.width; visible: root.summaryError !== ""; text: root.summaryError; color: Color.urgent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall; wrapMode: Text.Wrap }
                                    Text { width: parent.width; visible: root.errorText !== ""; text: root.errorText; color: Color.urgent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall; wrapMode: Text.Wrap }
                                    Row {
                                        spacing: 9
                                        Ui.Button { text: "Draw again"; focusable: true; enabled: root.busyAction === ""; onClicked: root.redraw() }
                                        Ui.Button { text: root.widgetEnabled ? "Hide desktop card" : "Show desktop card"; focusable: true; onClicked: root.toggleWidget() }
                                        Ui.Button { visible: root.adapterAvailable; text: summaryProc.running ? "Zephyr is reading…" : "Ask Zephyr"; focusable: true; enabled: !summaryProc.running && !!root.reading; onClicked: root.summarize() }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
