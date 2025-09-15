import json, random, time
from mqtt_helpers import make_client, topic

SENSOR_ID = "dht1"

def read_fake_dht():
    temp = round(random.uniform(22.0, 34.0), 2)
    hum = round(random.uniform(35.0, 65.0), 2)
    return {"temperature": temp, "humidity": hum}

client = make_client(f"emu-{SENSOR_ID}")
client.loop_start()

while True:
    reading = read_fake_dht()
    reading["sensor_id"] = SENSOR_ID
    client.publish(topic("sensors", SENSOR_ID), json.dumps(reading), qos=1)
    print("DHT ->", reading)
    time.sleep(3)
