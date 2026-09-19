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
    property string themedDirectory: ""
    property string themeRequestKey: ""
    property bool themeQueued: false
    readonly property string paletteKey: [String(Color.background), String(Color.foreground), String(Color.accent), String(Color.muted)].join("|")
    readonly property var card: reading && reading.card ? reading.card : ({})
    readonly property string orientation: reading && reading.reversed ? "REVERSED" : "UPRIGHT"
    readonly property string cardImage: card.art ? Util.fileUrl((themedDirectory || pluginDir) + "/" + card.art) : ""
    readonly property string backImage: Util.fileUrl((themedDirectory || pluginDir) + "/assets/card-back.svg")
    onPaletteKeyChanged: themeDelay.restart()
    Component.onCompleted: themeDelay.restart()

    function requestTheme() {
        if (themeProc.running) { themeQueued = true; return }
        themeQueued = false
        themeRequestKey = paletteKey
        themeProc.command = ["/usr/bin/python3", "-B", pluginDir + "/deck/theme_deck.py",
                             "--background", String(Color.background),
                             "--foreground", String(Color.foreground),
                             "--accent", String(Color.accent),
                             "--muted", String(Color.muted)]
        themeProc.running = true
    }

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
                readingWindow.resetForDraw()
                cardArrival = 0
                arrivalAnimation.restart()
            }
        } catch (e) { errorText = String(e) }
    }

    function openReading() {
        readingWindow.resetForDraw()
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
    function redraw() { readingWindow.resetForDraw(); doAction("redraw") }
    function summarize() {
        if (!reading || summaryProc.running || !adapterAvailable) return
        summaryError = ""
        summaryText = ""
        summaryProc.command = [adapter, reading.drawnAt]
        summaryProc.running = true
    }

    Timer { id: themeDelay; interval: 160; onTriggered: root.requestTheme() }
    Process {
        id: themeProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    if (result.ok && result.directory && root.themeRequestKey === root.paletteKey)
                        root.themedDirectory = result.directory
                    else if (root.themeRequestKey !== root.paletteKey) root.themeQueued = true
                } catch (e) { /* bundled SVGs remain available */ }
            }
        }
        onExited: function(code) {
            if (root.themeQueued || root.themeRequestKey !== root.paletteKey) themeDelay.restart()
        }
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
        function flip(): void { readingWindow.turn() }
        function guide(): void { root.openReading(); readingWindow.page = "guide"; readingWindow.flipProgress = 1 }
        function widget(): void { root.toggleWidget() }
        function status(): string { return JSON.stringify({open: root.overlayOpen, widget: root.widgetEnabled, day: root.day, card: root.card.id || "", face: readingWindow.flipProgress > 0.5 ? "details" : "art", themeReady: root.themedDirectory !== ""}) }
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

    CardOverlay {
        id: readingWindow
        screen: Quickshell.screens[0]
        visible: root.overlayPresent
        opened: root.overlayOpen
        reveal: root.reveal
        arrival: root.cardArrival
        reading: root.reading
        guide: root.guide
        day: root.day
        cardImage: root.cardImage
        backImage: root.backImage
        summary: root.summaryText
        summaryError: root.summaryError
        errorText: root.errorText
        summaryBusy: summaryProc.running
        adapterAvailable: root.adapterAvailable
        drawBusy: root.busyAction !== ""
        widgetEnabled: root.widgetEnabled
        onCloseRequested: root.closeReading()
        onRedrawRequested: root.redraw()
        onSummaryRequested: root.summarize()
        onWidgetRequested: root.toggleWidget()
    }
}
