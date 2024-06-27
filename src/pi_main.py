from pi_camera import Camera
from network import MQTTClient

import picamera
import io
import base64
import time

mqtt_topic_send = "moosinator/windows"
mqtt_topic_receive = "moosinator/pi"
client = MQTTClient("raspberry_pi_client", '192.168.0.45', 1883, mqtt_topic_receive)
start = time.time()

def capture_and_publish_images(camera):
    stream = io.BytesIO()
    for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
        # Rewind the stream
        stream.seek(0)
        # Read the image data from the stream
        image_data = stream.read()
        # Encode the image data to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        # Publish the image
        client.publish(mqtt_topic_send, image_base64)
        global start
        time_elapsed = time.time() - start
        print(f"Message published [{int(1/time_elapsed)} FPS]")
        # Reset the stream for the next capture
        stream.seek(0)
        stream.truncate()
        # Sleep for a short while to control frame rate
        time.sleep(0.1)  # Adjust as needed

def main():
    resolution = (480, 360)
    with picamera.PiCamera(resolution=resolution) as camera:
        capture_and_publish_images(camera)

    client.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        client.disconnect()

main()