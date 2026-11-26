import os 
import traceback
import base64
import random
import socket
import requests
import paho.mqtt.client as mqtt
from os import getenv
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

INFLUXDB_URL = "http://10.64.44.156:8086" # Public IP: 194.177.207.38
MY_TEAM = socket.gethostname()

load_dotenv()

db_name = "team7_db"
broker_address = "10.64.44.156" # Public IP: 194.177.207.38
broker_port = 1883
topic = f"iot/{MY_TEAM}/#"
client_id = f"client_{random.randint(0, 1000)}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.username_pw_set(MY_TEAM, getenv("MQTT_PASSWORD"))


def insert_data(db_name, user, password, measurement, value, timestamp=None):
  line = f"{measurement} value={value}"
  if timestamp:
    line += f" {timestamp}"
  response = requests.post(f"{INFLUXDB_URL}/write", 
                            params={"db": db_name},
                            data=line,
                            auth=HTTPBasicAuth(MY_TEAM, getenv("MQTT_PASSWORD")))
  print("Insert data:", response.ok)

def on_message(client, userdata, msg):
   topic_parts = msg.topic.split("/")  # ['iot', 'teamN', '<timestamp>', 'image']
   if len(topic_parts) == 4 and topic_parts[3] == 'motion':
      value = int(msg.payload.decode())
      measurement = topic_parts[3]
      timestamp = topic_parts[2]      
      print("Timestamp:", timestamp)      
      insert_data(db_name, MY_TEAM, getenv("MQTT_PASSWORD"), "motion", value, timestamp)

   if len(topic_parts) == 4 and topic_parts[3] == 'images':
      timestamp = topic_parts[2]       
      try:
        encoded_image = msg.payload.decode()
        image_data = base64.b64decode(encoded_image)
        os.makedirs("images", exist_ok = True)
        filename = f"images/image_{timestamp}.jpg"
        with open(filename, "wb") as f:
          f.write(image_data)
          
        insert_data(db_name, MY_TEAM, getenv("MQTT_PASSWORD"),"images",timestamp)
      except Exception as e:
          print(f"Error while saving image {e}")    
          traceback.print_exc()
def main():
  try:
    client.on_message = on_message
    print("After on message")
    client.connect(broker_address, broker_port)
    print(topic)
    client.subscribe(topic)

    print(f"Subscribing to `{topic}`. Waiting for messages...")
    client.loop_forever()
  except KeyboardInterrupt:
    print("Receive Ctrl+C signal! Bye")
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
  main()

  exit(0)
