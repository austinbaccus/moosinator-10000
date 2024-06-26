import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, client_id, broker, broker_port, topic):
        self.client_id = client_id
        self.broker = broker
        self.broker_port = broker_port
        self.topic = topic

        # Create a new MQTT client instance
        self.client = mqtt.Client(self.client_id)

        # Attach the callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Connect to the broker
        self.client.connect(self.broker, self.broker_port, 60)

    def start(self):
        self.client.loop_start()

    def publish(self, topic, message):
        self.client.publish(topic, message)

    def on_message(self, client, userdata, message):
        print(f"Message received: {message.payload.decode()} on topic {message.topic}")

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        self.subscribe(self.topic)

    def subscribe(self, topic):
        self.client.subscribe(topic)