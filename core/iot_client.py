"""
IoT Communication Layer - MQTT Protocol
Target: SINTA 2 (Novelty: Remote Monitoring)
Author: 03TELE004
"""
import paho.mqtt.client as mqtt
import json
import time
import random

class IoTClient:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"PythonMonitor-{random.randint(0, 1000)}")
        self.broker = "broker.emqx.io" # Default Public Broker
        self.port = 1883
        
        # Buffer Data (Untuk menyimpan data terakhir dari ESP32)
        self.latest_data = {
            "temp": 0.0,
            "volt": 0.0,
            "curr": 0.0,
            "relay": True
        }
        self.is_connected = False
        self.last_received_time = 0 # Untuk deteksi device offline

        # Callback events
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def connect_broker(self, broker_address="broker.emqx.io"):
        try:
            self.broker = broker_address
            print(f"Connecting to MQTT Broker: {self.broker}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start() # Jalankan di background thread
            return True
        except Exception as e:
            print(f"Connection Failed: {e}")
            return False

    def disconnect_broker(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.is_connected = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT Broker!")
            self.is_connected = True
            # Subscribe ke topik data dari ESP32
            self.client.subscribe("smartamp/data")
            self.client.subscribe("smartamp/status")
        else:
            print(f"❌ Failed to connect, return code {rc}")
            self.is_connected = False

    def on_message(self, client, userdata, msg):
        """Saat ada pesan masuk dari ESP32"""
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            
            if topic == "smartamp/data":
                # Parsing JSON: {"temp": 45.0, "volt": 12.0 ...}
                data = json.loads(payload)
                self.latest_data = data # Update buffer
                self.last_received_time = time.time()
                # print(f"Data received: {data}") # Debug only
                
        except Exception as e:
            print(f"Error parsing JSON: {e}")

    def send_command(self, cmd):
        """Kirim perintah kontrol ke ESP32"""
        # cmd bisa "ON" atau "OFF"
        if self.is_connected:
            self.client.publish("smartamp/control/relay", cmd)
            print(f"Command Sent: {cmd}")

    def get_data(self):
        """Diambil oleh GUI untuk update grafik"""
        return self.latest_data

    def check_online_status(self):
        """Cek apakah ESP32 masih hidup (Heartbeat)"""
        # Jika tidak ada data > 5 detik, anggap Offline
        if time.time() - self.last_received_time > 5:
            return False
        return True