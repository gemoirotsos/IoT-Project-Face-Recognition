from pathlib import Path
import cv2
import base64
import time
import random
import socket
import logging
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from os import getenv
from dotenv import load_dotenv
from datetime import datetime
 
LOG_FILE: str = "stats.log"
PIR_PIN: int = 17
CAMERA_ID = 0
 
load_dotenv()
MY_TEAM = "team7"
broker_address = "10.64.44.156"
broker_port = 1883
topic = f"iot/{MY_TEAM}"
client_id = f"client_{random.randint(0, 1000)}"
 
# MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.username_pw_set(MY_TEAM, getenv("MQTT_PASSWORD"))
client.connect(broker_address, broker_port)
client.loop_start()
 
def config_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)
 
def config_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        filemode='w',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
 
def capture_image():
    cap = cv2.VideoCapture(CAMERA_ID)
    ret, frame = cap.read()
    cap.release()
 
    if not ret:
        print("Image not received")
        return None
 
    return frame
 
def publish_image(timestamp):
    frame = capture_image()
    if frame is not None:
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            image_bytes = buffer.tobytes()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            image_topic = f"{topic}/{timestamp}/images"
            print(f"[{timestamp}] Sending in-memory image to {image_topic}")
            client.publish(image_topic, encoded_image, qos=1)
        else:
            print("Failed to encode frame")
 
def publish_motion(timestamp):
    motion_topic = f"{topic}/{timestamp}/motion"
    print(f"[{timestamp}] Motion detected! Sending to {topic}/motion")
    client.publish(motion_topic,1, qos=1)
 
def main():
    config_gpio()
    config_logging()
    last_state = GPIO.input(PIR_PIN)
 
    try:
        while True:
            current_state = GPIO.input(PIR_PIN)
            time.sleep(0.5)
 
            if current_state == 1 and last_state == 0:
                timestamp = int(time.time()* 1_000_000_000)
                publish_motion(timestamp)
                time.sleep(2)
                publish_image(timestamp)
 
            last_state = current_state
            time.sleep(0.1)
 
    except KeyboardInterrupt:
        print("Received Ctrl+C, exiting...")
 
    finally:
        GPIO.cleanup()
        client.loop_stop()
        client.disconnect()
 
if __name__ == "__main__":
    main()
