import time
from mqtt_helpers import make_client, topic

client = make_client("tester-pub")
client.loop_start()
for i in range(1, 6):
    payload = f"Hello IoT #{i}"
    client.publish(topic("test"), payload, qos=1, retain=False)
    print("Published:", payload)
    time.sleep(1)
client.loop_stop()
client.disconnect()
