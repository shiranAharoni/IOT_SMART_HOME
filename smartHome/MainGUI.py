import sys, json
from PyQt5 import QtWidgets, QtCore
from mqtt_helpers import make_client, topic

BROKER_CLIENT_NAME = "main-gui"

class MqttThread(QtCore.QThread):
    sig_log = QtCore.pyqtSignal(str)
    sig_temp = QtCore.pyqtSignal(float)
    sig_hum = QtCore.pyqtSignal(float)
    sig_button = QtCore.pyqtSignal(str)
    sig_relay = QtCore.pyqtSignal(bool)
    sig_alert = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = None
        self._connected = False

    def on_message(self, client, userdata, msg):
        try:
            t = msg.topic
            p = msg.payload.decode("utf-8", errors="ignore")
            self.sig_log.emit(f"{t} | {p}")
            # parse selected topics
            if "sensors/dht1" in t:
                data = json.loads(p)
                if "temperature" in data:
                    self.sig_temp.emit(float(data["temperature"]))
                if "humidity" in data:
                    self.sig_hum.emit(float(data["humidity"]))
            elif "controls/button1" in t:
                data = json.loads(p)
                self.sig_button.emit(str(data.get("state","")))
            elif "actuators/relay1/state" in t:
                data = json.loads(p)
                self.sig_relay.emit(bool(data.get("on", False)))
            elif "alerts" in t:
                data = json.loads(p)
                self.sig_alert.emit(data)
        except Exception as e:
            self.sig_log.emit(f"[ERR] on_message: {e!r}")

    def run(self):
        try:
            self.client = make_client(BROKER_CLIENT_NAME, self.on_message)
            self.client.subscribe(topic("#"))
            self.sig_log.emit(f"Subscribed to {topic('#')}")
            self._connected = True
            self.client.loop_forever()
        except Exception as e:
            self.sig_log.emit(f"[ERR] MQTT connect: {e!r}")
            self._connected = False

    def disconnect(self):
        try:
            if self.client:
                self.client.disconnect()
        except Exception as e:
            self.sig_log.emit(f"[ERR] disconnect: {e!r}")

class MainWin(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Home — Main GUI")
        self.resize(760, 520)

        # Widgets
        self.lblTemp = QtWidgets.QLabel("Temperature: — °C")
        self.lblHum = QtWidgets.QLabel("Humidity: — %")
        self.lblBtn = QtWidgets.QLabel("Button: —")
        self.lblRelay = QtWidgets.QLabel("Relay: —")

        font_big = self.lblTemp.font()
        font_big.setPointSize(13)
        for w in (self.lblTemp, self.lblHum, self.lblBtn, self.lblRelay):
            w.setFont(font_big)

        self.btnConnect = QtWidgets.QPushButton("Connect & Subscribe")
        self.btnDisconnect = QtWidgets.QPushButton("Disconnect")
        self.btnDisconnect.setEnabled(False)

        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)

        self.alerts = QtWidgets.QTextEdit()
        self.alerts.setReadOnly(True)
        self.alerts.setPlaceholderText("Alerts/Warnings will appear here...")

        # Layout
        grid = QtWidgets.QGridLayout(self)
        grid.addWidget(self.lblTemp, 0, 0)
        grid.addWidget(self.lblHum, 0, 1)
        grid.addWidget(self.lblBtn, 1, 0)
        grid.addWidget(self.lblRelay, 1, 1)

        grid.addWidget(self.btnConnect, 2, 0)
        grid.addWidget(self.btnDisconnect, 2, 1)

        grid.addWidget(QtWidgets.QLabel("Alerts / Warnings"), 3, 0, 1, 2)
        grid.addWidget(self.alerts, 4, 0, 1, 2)

        grid.addWidget(QtWidgets.QLabel("Raw Messages Log"), 5, 0, 1, 2)
        grid.addWidget(self.log, 6, 0, 1, 2)

        # Thread
        self.t = None

        # Signals
        self.btnConnect.clicked.connect(self.start_mqtt)
        self.btnDisconnect.clicked.connect(self.stop_mqtt)

    def start_mqtt(self):
        if self.t and self.t.isRunning():
            return
        self.t = MqttThread()
        self.t.sig_log.connect(self.append_log)
        self.t.sig_temp.connect(self.on_temp)
        self.t.sig_hum.connect(self.on_hum)
        self.t.sig_button.connect(self.on_btn)
        self.t.sig_relay.connect(self.on_relay)
        self.t.sig_alert.connect(self.on_alert)
        self.t.start()
        self.btnConnect.setEnabled(False)
        self.btnDisconnect.setEnabled(True)
        self.append_log("[INFO] MQTT thread started")

    def stop_mqtt(self):
        if self.t:
            self.t.disconnect()
            self.t.terminate()
            self.t.wait(1000)
            self.t = None
        self.btnConnect.setEnabled(True)
        self.btnDisconnect.setEnabled(False)
        self.append_log("[INFO] MQTT thread stopped")

    # Slots
    @QtCore.pyqtSlot(float)
    def on_temp(self, v):
        self.lblTemp.setText(f"Temperature: {v:.2f} °C")

    @QtCore.pyqtSlot(float)
    def on_hum(self, v):
        self.lblHum.setText(f"Humidity: {v:.2f} %")

    @QtCore.pyqtSlot(str)
    def on_btn(self, s):
        self.lblBtn.setText(f"Button: {s}")

    @QtCore.pyqtSlot(bool)
    def on_relay(self, on):
        self.lblRelay.setText("Relay: ON" if on else "Relay: OFF")

    @QtCore.pyqtSlot(dict)
    def on_alert(self, d):
        self.alerts.append(json.dumps(d))

    @QtCore.pyqtSlot(str)
    def append_log(self, line):
        self.log.append(line)

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWin()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
