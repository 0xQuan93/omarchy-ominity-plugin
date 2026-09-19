import QtQuick
import qs.Commons
import qs.Ui

BarWidget {
    id: root
    moduleName: "oxquan.ominity"
    implicitWidth: glyph.implicitWidth
    implicitHeight: glyph.implicitHeight

    function service() {
        return root.bar && root.bar.shell ? root.bar.shell.serviceFor("oxquan.ominity") : null
    }

    WidgetButton {
        id: glyph
        anchors.fill: parent
        bar: root.bar
        text: "✦"
        fontSize: Style.font.iconLarge
        foreground: Color.accent
        horizontalMargin: 9
        tooltipText: "Ominity · pull today's tarot card\nRight click · toggle desktop card"
        onPressed: function(button) {
            var reading = root.service()
            if (!reading) return
            if (button === Qt.RightButton) reading.toggleWidget()
            else reading.toggleReading()
        }
    }
}
