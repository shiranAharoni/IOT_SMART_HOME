import json
from mqtt_helpers import make_client, topic

RELAY_ID = "relay1"
state = {"relay_id": RELAY_ID, "on": False}

def on_message(client, userdata, msg):
    global state
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        desired = bool(data.get("on", False))
        state["on"] = desired
        print("Relay set ->", state)
        client.publish(topic("actuators", RELAY_ID, "state"), json.dumps(state), qos=1)
    except Exception as e:
        print("Error:", e)

client = make_client(f"emu-{RELAY_ID}", on_message)
client.subscribe(topic("actuators", RELAY_ID, "set"))
print("Relay listening on", topic("actuators", RELAY_ID, "set"))
client.loop_forever()
