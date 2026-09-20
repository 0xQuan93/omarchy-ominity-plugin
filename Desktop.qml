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
    property bool constellationOpen: false
    property var constellationStats: ({})
    property var constellationHistory: []
    property string constellationError: ""
    property var historicalReading: null
    property var historicalJournal: ({})
    property string historicalError: ""
    property string historicalDay: ""
    property string archiveMessage: ""
    property string archiveAction: ""
    property var journal: ({firstImpression: "", eveningReflection: ""})
    property string journalLoadedDay: ""
    property string journalAction: ""
    property string journalPayload: ""
    property string journalRequestDay: ""
    property string journalError: ""
    property string journalSaved: ""
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
    readonly property string bodyFont: "Noto Sans"
    readonly property string displayFont: "Noto Serif"
    readonly property string paletteKey: [String(Color.background), String(Color.foreground), String(Color.accent), String(Color.muted)].join("|")
    readonly property var card: reading && reading.card ? reading.card : ({})
    readonly property string orientation: reading && reading.reversed ? "REVERSED" : "UPRIGHT"
    readonly property string cardImage: reading && reading.artworkPath ? Util.fileUrl(reading.artworkPath) : (card.art ? Util.fileUrl((themedDirectory || pluginDir) + "/" + card.art) : "")
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
        var command = ["/usr/bin/python3", "-B", pluginDir + "/ominity.py", action]
        if (action === "today" || action === "redraw") {
            command.push("--background", String(Color.background),
                         "--foreground", String(Color.foreground),
                         "--accent", String(Color.accent),
                         "--muted", String(Color.muted))
        }
        stateProc.command = command
        stateProc.running = true
    }

    function acceptState(raw) {
        try {
            var next = JSON.parse(raw)
            if (!next.ok) throw new Error(next.error || "Could not read the deck")
            var oldStamp = reading ? reading.drawnAt : ""
            var oldDay = day
            day = next.day || ""
            if (day !== oldDay) {
                journalLoadedDay = ""
                journal = ({firstImpression: "", eveningReflection: ""})
                journalSaved = ""
            }
            reading = next.reading
            widgetEnabled = next.widget === true
            if (reading && oldStamp !== reading.drawnAt) {
                summaryText = ""
                summaryError = ""
                readingWindow.resetForDraw()
                cardArrival = 0
                arrivalWait.polls = 0
                arrivalWait.restart()
            }
        } catch (e) { errorText = String(e) }
    }

    function openReading() {
        constellationOpen = false
        readingWindow.resetForDraw()
        overlayOpen = true
        overlayPresent = true
        animateReveal(true)
        doAction("today")
    }

    function closeReading() {
        constellationOpen = false
        overlayOpen = false
        animateReveal(false)
    }

    function openConstellation() {
        constellationError = ""
        constellationOpen = true
        if (!statsProc.running) {
            statsProc.command = ["/usr/bin/python3", "-B", pluginDir + "/ominity.py", "stats"]
            statsProc.running = true
        }
        if (!historyProc.running) {
            historyProc.command = ["/usr/bin/python3", "-B", pluginDir + "/ominity.py", "history"]
            historyProc.running = true
        }
    }

    function runArchive(action, path) {
        if (archiveProc.running) return
        archiveAction = action
        archiveMessage = ""
        archiveProc.command = ["/usr/bin/python3", "-B", pluginDir + "/ominity.py", action, "--path", path]
        archiveProc.running = true
    }

    function openHistoricalDay(requestedDay) {
        if (dayProc.running) return
        historicalDay = requestedDay
        historicalReading = null
        historicalJournal = ({})
        historicalError = ""
        dayProc.command = ["/usr/bin/python3", "-B", pluginDir + "/ominity.py", "day", "--day", requestedDay]
        dayProc.running = true
    }

    function animateReveal(open) {
        revealAnimation.stop()
        revealAnimation.to = open ? 1 : 0
        revealAnimation.duration = Math.max(120, Math.round((open ? 440 : 370) * Math.abs(revealAnimation.to - reveal)))
        revealAnimation.easing.type = open ? Easing.OutQuart : Easing.InCubic
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

    function loadJournal() {
        if (!day || journalLoadedDay === day || journalProc.running) return
        journalAction = "journal-get"
        journalRequestDay = day
        journalError = ""
        journalProc.command = ["/usr/bin/python3", "-B", pluginDir + "/ominity.py", "journal-get", "--day", day]
        journalProc.running = true
    }

    function saveJournal(firstImpression, eveningReflection) {
        if (!day || journalProc.running) return
        journalAction = "journal-save"
        journalRequestDay = day
        journalError = ""
        journalSaved = ""
        journalPayload = JSON.stringify({firstImpression: firstImpression, eveningReflection: eveningReflection}) + "\n"
        journalProc.command = ["/usr/bin/python3", "-B", pluginDir + "/ominity.py", "journal-save", "--day", day]
        journalProc.running = true
    }

    Timer { id: themeDelay; interval: 160; onTriggered: root.requestTheme() }
    Timer {
        id: arrivalWait
        property int polls: 0
        interval: 40
        repeat: true
        onTriggered: {
            polls += 1
            if (readingWindow.artworkFailed && root.themedDirectory !== "") root.themedDirectory = ""
            if (readingWindow.artworkReady || polls >= 60) {
                stop()
                arrivalAnimation.restart()
            }
        }
    }
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
    Process {
        id: statsProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    if (!result.ok) throw new Error(result.error || "Statistics are unavailable")
                    root.constellationStats = result
                } catch (e) { root.constellationError = String(e) }
            }
        }
        onExited: function(code) { if (code !== 0 && !root.constellationError) root.constellationError = "Constellation could not read the local archive." }
    }
    Process {
        id: historyProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    if (!result.ok) throw new Error(result.error || "History is unavailable")
                    root.constellationHistory = result.days || []
                } catch (e) { root.constellationError = String(e) }
            }
        }
        onExited: function(code) { if (code !== 0 && !root.constellationError) root.constellationError = "Constellation could not read the local archive." }
    }
    Process {
        id: journalProc
        stdinEnabled: true
        onStarted: if (root.journalAction === "journal-save") write(root.journalPayload)
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    if (!result.ok) throw new Error(result.error || "Journal is unavailable")
                    if (root.journalRequestDay !== root.day) return
                    if (root.journalAction === "journal-get") {
                        root.journal = result.journal || ({firstImpression: "", eveningReflection: ""})
                        root.journalLoadedDay = root.journalRequestDay
                    } else {
                        root.journalLoadedDay = root.journalRequestDay
                        root.journalSaved = "Saved on this machine."
                    }
                } catch (e) { root.journalError = String(e) }
            }
        }
        onExited: function(code) {
            root.journalPayload = ""
            if (code !== 0 && !root.journalError) root.journalError = "The journal could not be saved."
        }
    }
    Process {
        id: archiveProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    if (!result.ok) throw new Error(result.error || "Archive operation failed")
                    root.archiveMessage = root.archiveAction === "archive-export"
                        ? "Verified archive created: " + (result.path || "")
                        : "Archive verified and imported: " + String(result.importedDays || 0) + " new daily records."
                    if (root.archiveAction === "archive-import") root.openConstellation()
                } catch (e) { root.archiveMessage = String(e) }
            }
        }
        onExited: function(code) { if (code !== 0 && !root.archiveMessage) root.archiveMessage = "Archive operation failed." }
    }
    Process {
        id: dayProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    if (!result.ok || result.day !== root.historicalDay) throw new Error(result.error || "Historical reading is unavailable")
                    root.historicalReading = result.reading
                    root.historicalJournal = result.journal || ({})
                } catch (e) { root.historicalError = String(e) }
            }
        }
        onExited: function(code) { if (code !== 0 && !root.historicalError) root.historicalError = "Historical reading could not be opened." }
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
        target: root; property: "reveal"
        duration: 440
        easing.type: Easing.OutQuart
        onStopped: if (!root.overlayOpen && root.reveal <= 0.001) root.overlayPresent = false
    }
    NumberAnimation {
        id: arrivalAnimation
        target: root; property: "cardArrival"; from: 0; to: 1
        duration: 930; easing.type: Easing.InOutCubic
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
        function journal(): void { root.openReading(); readingWindow.page = "journal"; readingWindow.flipProgress = 1; root.loadJournal() }
        function widget(): void { root.toggleWidget() }
        function constellation(): void { root.openConstellation() }
        function archive(): void { root.openConstellation(); constellationWindow.archiveOpen = true; constellationWindow.archiveMode = "export"; constellationWindow.archivePath = constellationWindow.archiveDefaultPath }
        function history(requestedDay: string): void { root.openConstellation(); constellationWindow.historyOpen = true; root.openHistoricalDay(requestedDay) }
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
                Text { renderType: Text.CurveRendering; text: "✦  O M I N I T Y   /   " + (root.day || "TODAY"); color: Color.accent; font.family: root.bodyFont; font.pixelSize: Math.max(11, Style.font.caption) }
                Text { renderType: Text.CurveRendering; width: parent.width; text: root.reading ? root.card.title : "A card waits for you"; color: Color.popups.text; font.family: root.displayFont; font.pixelSize: 27; elide: Text.ElideRight }
                Text { renderType: Text.CurveRendering; width: parent.width; text: root.reading ? root.orientation + "  ·  " + (root.card.keywords || []).slice(0, 2).join(" / ") : "A small ritual for the day ahead."; color: Color.popups.text; opacity: 0.8; font.family: root.bodyFont; font.pixelSize: Math.max(12, Style.font.bodySmall); elide: Text.ElideRight }
                Text { renderType: Text.CurveRendering; text: root.reading ? "OPEN THE READING  ↗" : "PULL TODAY'S CARD  ↗"; color: Color.accent; font.family: root.bodyFont; font.pixelSize: Math.max(12, Style.font.bodySmall) }
            }
            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.openReading() }
        }
    }

    CardOverlay {
        id: readingWindow
        screen: Quickshell.screens[0]
        visible: root.overlayPresent && !root.constellationOpen
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
        journal: root.journal
        journalBusy: journalProc.running
        journalError: root.journalError
        journalSaved: root.journalSaved
        onCloseRequested: root.closeReading()
        onRedrawRequested: root.redraw()
        onSummaryRequested: root.summarize()
        onWidgetRequested: root.toggleWidget()
        onConstellationRequested: root.openConstellation()
        onJournalLoadRequested: root.loadJournal()
        onJournalSaveRequested: function(firstImpression, eveningReflection) { root.saveJournal(firstImpression, eveningReflection) }
    }

    Constellation {
        id: constellationWindow
        screen: Quickshell.screens[0]
        visible: root.constellationOpen
        opened: root.constellationOpen
        stats: root.constellationStats
        entries: root.constellationHistory
        errorText: root.constellationError
        archiveDefaultPath: root.home + "/Documents/Ominity-" + (root.day || Qt.formatDate(new Date(), "yyyy-MM-dd")) + ".zip"
        archiveMessage: root.archiveMessage
        archiveBusy: archiveProc.running
        fallbackDirectory: root.themedDirectory || root.pluginDir
        historyReading: root.historicalReading
        historyJournal: root.historicalJournal
        historyBusy: dayProc.running
        historyError: root.historicalError
        onCloseRequested: root.constellationOpen = false
        onDayRequested: function(requestedDay) { root.openHistoricalDay(requestedDay) }
        onExportRequested: function(path) { root.runArchive("archive-export", path) }
        onImportRequested: function(path) { root.runArchive("archive-import", path) }
    }
}
