import json, ssl, random
from pathlib import Path
import paho.mqtt.client as mqtt

def load_config(path: str = "config.json") -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def make_client(client_id_suffix: str = "client", on_message=None) -> mqtt.Client:
    cfg = load_config()
    client_id = f"{cfg.get('client_prefix','iot-')}{client_id_suffix}-{random.randint(1000,9999)}"
    c = mqtt.Client(client_id=client_id, clean_session=True)
    c.username_pw_set(cfg["username"], cfg["password"])
    c.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
    c.tls_insecure_set(False)
    if on_message:
        c.on_message = on_message
    c.connect(cfg["host"], int(cfg.get("port", 8883)))
    return c

def topic(*parts: str) -> str:
    base = load_config().get("base_topic","home")
    return "/".join([base, *parts])
