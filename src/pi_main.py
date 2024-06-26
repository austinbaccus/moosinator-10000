from pi_camera import Camera
from network import MQTTClient
import time

def main():
    camera = Camera()
    camera.start()

    mqtt_topic_send = "moosinator/windows"
    mqtt_topic_receive = "moosinator/pi"

    client = MQTTClient("raspberry_pi_client", '192.168.0.45', 1883, mqtt_topic_receive)

    try:
        while True:
            time.sleep(5)
            client.publish(mqtt_topic_send, "Hello from Pi!")
    except KeyboardInterrupt:
        print("Disconnecting...")
        client.disconnect()

main()