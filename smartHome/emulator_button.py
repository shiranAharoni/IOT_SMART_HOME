import json, time, itertools
from mqtt_helpers import make_client, topic

BUTTON_ID = "button1"
client = make_client(f"emu-{BUTTON_ID}")
client.loop_start()

states = itertools.cycle(["pressed", "released"])
while True:
    state = next(states)
    payload = {"button_id": BUTTON_ID, "state": state}
    client.publish(topic("controls", BUTTON_ID), json.dumps(payload), qos=1)
    print("Button ->", payload)
    time.sleep(5)
