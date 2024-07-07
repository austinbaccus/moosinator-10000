from network import MQTTClient
import picamera
import io
import base64
import time
import json

with open('settings.json', 'r') as file:
    config = json.load(file)

target_resolution = config["TargetResolution"]

client = MQTTClient("raspberry_pi_client", config["RaspberryPiIP"], config["RaspberryPiPort"], config["MqttTopicPi"])
start = time.time()

def capture_and_publish_image_stream(camera, target_fps):
    stream = io.BytesIO()
    for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
        stream.seek(0) # Rewind the stream
        image_data = stream.read() # Read the image data from the stream
        image_base64 = base64.b64encode(image_data).decode('utf-8') # Encode the image data to base64

        # FPS
        global start
        time_elapsed = time.time() - start

        # If we're ahead of our FPS target, wait.
        target_time_between_captures = 1.0/target_fps
        time_to_wait = target_time_between_captures - time_elapsed
        if (time_to_wait > 0):
            time.sleep(time_to_wait)
            time_elapsed = time_elapsed + time_to_wait
        else:
            time_to_wait = 0

        json_msg = json.dumps({"ir_camera_data": image_base64})

        client.publish(config["MqttTopicWindows"], json_msg)
        print("Message published [{} FPS] [Waited for {} seconds]".format(round(1/time_elapsed, 1), round(time_to_wait, 2)))
        start = time.time()

        # Reset the stream for the next capture
        stream.seek(0)
        stream.truncate()

def command_received(command):
    print("command received: {}".format(command))

def main():
    client.client.on_message = command_received
    print("Listening on topic: {}".format(config["MqttTopicPi"]))
    client.start()

    resolution = (config["TargetResolution"][0], config["TargetResolution"][1])
    
    try:
        with picamera.PiCamera(resolution=resolution) as camera:
            capture_and_publish_image_stream(camera, config["TargetFPS"])
    except KeyboardInterrupt:
        client.disconnect()

main()