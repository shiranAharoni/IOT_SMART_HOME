import json, sqlite3
from datetime import datetime
from mqtt_helpers import make_client, topic

DB_PATH = "smart_home.db"

# --- Relay auto-control settings ---
RELAY_ID = "relay1"
TEMP_ON  = 30.0  # turn ON when temperature >= 30.0
TEMP_OFF = 29.0  # turn OFF when temperature <= 29.0
relay_on = False
# -----------------------------------

# Initialize SQLite DB
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    sensor_id TEXT,
    temperature REAL,
    humidity REAL
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    source TEXT,
    type TEXT,
    details TEXT
)
""")
conn.commit()

def now():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

# Function to send relay command
def set_relay(client, on: bool):
    """
    Publish a command to the relay emulator to set its state.
    """
    global relay_on
    payload = {"relay_id": RELAY_ID, "on": bool(on)}
    client.publish(topic("actuators", RELAY_ID, "set"), json.dumps(payload), qos=1)
    relay_on = bool(on)
    print(f"[CTRL] relay -> {'ON' if relay_on else 'OFF'}")

# Main on_message callback
def on_message(client, userdata, msg):
    global relay_on
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        ts = now()

        # --- Sensor readings (DHT) ---
        if "sensors/dht1" in msg.topic:
            temp = float(payload.get("temperature"))
            hum = float(payload.get("humidity"))
            sid = payload.get("sensor_id", "dht1")

            # Write reading to DB
            cur.execute("INSERT INTO readings(ts, sensor_id, temperature, humidity) VALUES (?,?,?,?)",
                        (ts, sid, temp, hum))
            conn.commit()

            # Send alert if temp >= TEMP_ON
            if temp >= TEMP_ON:
                alert = {"level": "ALARM", "reason": "TEMP_HIGH", "value": temp, "ts": ts}
                client.publish(topic("alerts"), json.dumps(alert), qos=1)
                cur.execute("INSERT INTO events(ts, source, type, details) VALUES (?,?,?,?)",
                            (ts, "DataManager", "ALERT", json.dumps(alert)))
                conn.commit()

            # --- Relay auto-control with hysteresis ---
            if (not relay_on) and (temp >= TEMP_ON):
                set_relay(client, True)
            elif relay_on and (temp <= TEMP_OFF):
                set_relay(client, False)
            # ------------------------------------------

            print(f"[DB] readings <- {sid} T={temp} H={hum}")

        # --- Button control events ---
        elif "controls/button1" in msg.topic:
            cur.execute("INSERT INTO events(ts, source, type, details) VALUES (?,?,?,?)",
                        (ts, "button", "CONTROL", json.dumps(payload)))
            conn.commit()
            print("[DB] control event", payload)

        # --- Relay state echo (optional) ---
        elif f"actuators/{RELAY_ID}/state" in msg.topic:
            on = bool(payload.get("on", False))
            relay_on = on
            print(f"[INFO] relay state echoed -> {'ON' if on else 'OFF'}")

        else:
            print("[Info] Unhandled topic:", msg.topic)

    except Exception as e:
        print("on_message error:", e)

# MQTT client setup
client = make_client("data-manager", on_message)
client.subscribe(topic("sensors", "dht1"))
client.subscribe(topic("controls", "button1"))
client.subscribe(topic("actuators", RELAY_ID, "state"))

print("DataManager subscribed to:",
      topic("sensors", "dht1"),
      "and", topic("controls", "button1"),
      "and", topic("actuators", RELAY_ID, "state"))

client.loop_forever()
