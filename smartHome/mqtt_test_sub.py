from mqtt_helpers import make_client, topic

def on_message(client, userdata, msg):
    print(f"[MSG] {msg.topic}: {msg.payload.decode('utf-8', errors='ignore')}")

client = make_client("tester-sub", on_message)
client.subscribe("shiran_home/#")
print("Subscribed to shiran_home/#")
client.loop_forever()
