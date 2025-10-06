#!/usr/bin/env python3
"""
IoT Cooking Monitor System
Integrates multiple sensors, camera, PostgreSQL database and Linux server
Components:
- C4001 mmWave Presence Sensor (UART)
- HC-SR501 PIR sensor (GPIO18)
- MLX90640 Thermal Camera (I2C)
- Raspberry Pi Camera
- Dual-color LED (Red: GPIO27, Green: GPIO22)
- Button (GPIO17)
- PostgreSQL database
- Linux server for time sync and image storage
"""

import RPi.GPIO as GPIO
import time
import threading
import os
import sys
import subprocess
import shlex
import psycopg as pg
from datetime import datetime, timedelta
from picamera2 import Picamera2
from queue import Queue
import signal
from dotenv import load_dotenv
import getpass
import board
import busio
import adafruit_mlx90640

from PIL import Image
import io

# Add DFRobot library path
sys.path.append("../")
from DFRobot_C4001 import *

# GPIO Pin Configuration
BUTTON_PIN = 17
PIR_PIN = 18
LED_RED_PIN = 27
LED_GREEN_PIN = 22

# Load Database Configuration
load_dotenv()

# Database Configuration

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

IMDB_HOST = os.getenv("IMDB_HOST")
IMDB_USER = os.getenv("IMDB_USER")
IMDB_PASSWORD = os.getenv("IMDB_PASSWORD")

# Camera Configuration
IMAGE_FOLDER = "motion_images"
IMDB_FOLDER = "~/iot2025"
IMAGE_INTERVAL = 30  # 2 minutes in seconds

# Thermal Camera Configuration
THERMAL_INTERVAL = 15  # 30 seconds


class TimeManager:
    """Manages time synchronization with Linux server"""

    def __init__(self, host, username, password=None):
        self.host = host
        self.username = username
        self.password = password or getpass.getpass(f"Password for {username}@{host}: ")
        self.time_delta = timedelta(0)
        self.sync_time()

    def sync_time(self):
        """Synchronize time with Linux server"""
        try:
            cmd = [
                'sshpass', '-p', self.password,
                'ssh', '-o', 'StrictHostKeyChecking=no',
                f'{self.username}@{self.host}',
                'date +"%Y-%m-%d %H:%M:%S"'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                server_time_str = result.stdout.strip()
                server_time = datetime.strptime(server_time_str, "%Y-%m-%d %H:%M:%S")
                local_time = datetime.now()
                self.time_delta = server_time - local_time

                print(f"Time synchronized with server")
                print(f"Server time: {server_time}")
                print(f"Local time: {local_time}")
                return True
            else:
                print(f"Time sync failed: {result.stderr}")
                return False

        except FileNotFoundError:
            print("sshpass not found. Install with: sudo apt install sshpass")
            print("Using local time instead")
            return False
        except Exception as e:
            print(f"Time sync error: {e}")
            print("Using local time instead")
            return False

    def get_synced_time(self):
        """Get current time adjusted with server delta"""
        return datetime.now() + self.time_delta


class ImageTransferManager:
    """Manages image transfer to Linux server"""

    def __init__(self, host, username, password, remote_base_path):
        self.host = host
        self.username = username
        self.password = password
        self.remote_base_path = remote_base_path

    def create_remote_directory(self, remote_dir):
        """Create directory on remote server"""
        try:
            cmd = [
                'sshpass', '-p', self.password,
                'ssh', '-o', 'StrictHostKeyChecking=no',
                f'{self.username}@{self.host}',
                f'mkdir -p {remote_dir}'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0

        except Exception as e:
            print(f"Remote directory creation error: {e}")
            return False

    def transfer_image_scp(self, local_path, remote_path):
        """Transfer image using sshpass + scp (recommended for Raspberry Pi 3)"""
        try:
            cmd = [
                'sshpass', '-p', self.password,
                'scp', '-o', 'StrictHostKeyChecking=no',
                local_path,
                f'{self.username}@{self.host}:{remote_path}'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return True
            else:
                print(f"SCP transfer failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"SCP transfer error: {e}")
            return False


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""

    def __init__(self, host, port, dbname, user, password, time_manager):
        self.conn_str = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
        self.current_session = 0
        self.time_manager = time_manager
        self.init_database()

    def init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            with pg.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    # Create tables if they don't exist
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS motion1 (
                            id SERIAL PRIMARY KEY,
                            session INT,
                            datetime TIMESTAMP,
                            value BOOLEAN
                        )
                    """)

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS motion2 (
                            id SERIAL PRIMARY KEY,
                            session INT,
                            datetime TIMESTAMP,
                            value BOOLEAN
                        )
                    """)

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS switch (
                            id SERIAL PRIMARY KEY,
                            session INT,
                            datetime TIMESTAMP,
                            status BOOLEAN
                        )
                    """)

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS temperature (
                            id SERIAL PRIMARY KEY,
                            session INT,
                            datetime TIMESTAMP,
                            value DECIMAL(6,2) NOT NULL
                        )
                    """)

                    # Get the latest session number
                    cur.execute("SELECT MAX(session) FROM switch")
                    result = cur.fetchone()
                    if result[0] is not None:
                        self.current_session = result[0]

                    print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
            sys.exit(1)

    def insert_motion(self, table_name, session, value):
        """Insert motion detection data"""
        try:
            with pg.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    synced_time = self.time_manager.get_synced_time()
                    cur.execute(
                        f"INSERT INTO {table_name} (session, datetime, value) VALUES (%s, %s, %s)",
                        (session, synced_time, value)
                    )
                conn.commit()
            return True
        except Exception as e:
            print(f"Database insert error: {e}")
            return False

    def insert_switch(self, session, value):
        """Insert switch state data"""
        # return self.insert_motion('switch', session, value)
        try:
            with pg.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    synced_time = self.time_manager.get_synced_time()
                    cur.execute(
                        f"INSERT INTO {'switch'} (session, datetime, status) VALUES (%s, %s, %s)",
                        (session, synced_time, value)
                    )
                conn.commit()
            return True
        except Exception as e:
            print(f"Database insert error: {e}")
            return False

    def insert_temperature(self, session, temperature):
        """Insert temperature data"""
        # return self.insert_motion('temperature', session, value)
        try:
            with pg.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    synced_time = self.time_manager.get_synced_time()
                    cur.execute(
                        f"INSERT INTO {'temperature'} (session, datetime, value) VALUES (%s, %s, %s)",
                        (session, synced_time, temperature)
                    )
                conn.commit()
            return True
        except Exception as e:
            print(f"Database insert error: {e}")
            return False


class MLX90640Sensor:
    """Manages MLX90640 thermal camera sensor"""

    def __init__(self):
        self.mlx = None
        self.frame = [0] * 768  # 32x24 = 768 pixels
        self.setup()

    def setup(self):
        """Initialize MLX90640 sensor"""
        try:
            # Create I2C bus
            i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)

            # Initialize MLX90640
            self.mlx = adafruit_mlx90640.MLX90640(i2c)

            # Set refresh rate (2Hz for balanced performance)
            self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

            print(f"MLX90640 thermal sensor initialized successfully")
            print(f"Refresh rate: {self.mlx.refresh_rate}Hz")
            return True

        except Exception as e:
            print(f"MLX90640 initialization error: {e}")
            print("Thermal monitoring will be disabled")
            return False

    def get_max_temperature(self):
        """Get the maximum temperature from the sensor"""
        if not self.mlx:
            return None

        try:
            # Get temperature data
            self.mlx.getFrame(self.frame)

            # Find and return maximum temperature
            max_temp = max(self.frame)
            return max_temp

        except Exception as e:
            print(f"Error reading thermal data: {e}")
            return None

    def get_temperature_stats(self):
        """Get temperature statistics (max, min, average)"""
        if not self.mlx:
            return None

        try:
            # Get temperature data
            self.mlx.getFrame(self.frame)

            # Calculate statistics
            max_temp = max(self.frame)
            min_temp = min(self.frame)
            avg_temp = sum(self.frame) / len(self.frame)

            return {
                'max': max_temp,
                'min': min_temp,
                'avg': avg_temp
            }

        except Exception as e:
            print(f"Error calculating thermal stats: {e}")
            return None


class C4001Sensor:
    """Manages DFRobot C4001 mmWave sensor"""

    def __init__(self):
        self.radar = DFRobot_C4001_UART(9600)
        self.setup()

    def setup(self):
        """Initialize C4001 sensor"""
        while not self.radar.begin():
            print("C4001 sensor initialization failed! Retrying...")
            time.sleep(1)

        # Configure sensor
        self.radar.set_sensor_mode(EXIST_MODE)
        self.radar.set_detect_thres(11, 1200, 11)
        self.radar.set_detection_range(30, 1000, 1000)
        self.radar.set_trig_sensitivity(1)
        self.radar.set_keep_sensitivity(1)
        self.radar.set_delay(100, 4)
        self.radar.set_pwm(50, 0, 10)
        self.radar.set_io_polaity(1)

        print("C4001 sensor initialized successfully")

    def detect_motion(self):
        """Check for motion detection"""
        try:
            return self.radar.motion_detection() == 1
        except:
            return False


class CameraManager:
    """Manages Raspberry Pi Camera operations"""

    def __init__(self, local_base_path, time_manager, transfer_manager):
        self.local_base_path = local_base_path
        self.time_manager = time_manager
        self.transfer_manager = transfer_manager
        self.camera = None
        self.current_session_folder = None
        self.setup_camera()

    def setup_camera(self):
        """Initialize camera"""
        try:
            self.camera = Picamera2()

            # Get camera properties
            camera_properties = self.camera.camera_properties
            sensor_resolution = camera_properties['PixelArraySize']

            config = self.camera.create_still_configuration(
                main={"size": sensor_resolution},  # Full HD
                buffer_count=1  # Memory optimization
            )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(2)  # Camera warm-up
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Camera initialization error: {e}")

    def create_session_folder(self, session_id):
        """Create folder for current session locally and remotely"""
        synced_time = self.time_manager.get_synced_time()
        folder_name = f"{session_id}"

        # Create local folder
        local_folder = os.path.join(self.local_base_path, folder_name)
        if not os.path.exists(local_folder):
            os.makedirs(local_folder)
            print(f"Created local folder: {local_folder}")

        # Create remote folder
        remote_folder = os.path.join(self.transfer_manager.remote_base_path, folder_name)
        if self.transfer_manager.create_remote_directory(remote_folder):
            print(f"Created remote folder: {remote_folder}")
        else:
            print(f"Failed to create remote folder: {remote_folder}")

        self.current_session_folder = folder_name
        return folder_name

    def capture_and_transfer_image(self, session_id):
        """Capture image and transfer to server"""
        if not self.current_session_folder:
            self.create_session_folder(session_id)

        try:
            # Generate filename with synced timestamp
            synced_time = self.time_manager.get_synced_time()
            timestamp = synced_time.strftime("%Y%m%d_%H%M%S")
            filename = f"img_{session_id}_{timestamp}.jpg"

            # Local path
            local_filepath = os.path.join(
                self.local_base_path,
                self.current_session_folder,
                filename
            )

            # Capture image
            image_buffer = io.BytesIO()
            self.camera.capture_file(image_buffer, format='jpeg')
            image_buffer.seek(0)

            # Open image with PIL and resize to 1080p
            img = Image.open(image_buffer)
            original_size = img.size

            # Calculate new size maintaining aspect ratio
            target_width = 1920
            target_height = 1080

            # Get original aspect ratio
            aspect_ratio = original_size[0] / original_size[1]

            # Calculate dimensions to maintain aspect ratio
            if aspect_ratio > (target_width / target_height):
                # Image is wider - fit to width
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                # Image is taller - fit to height
                new_height = target_height
                new_width = int(target_height * aspect_ratio)

            # Resize image using high-quality Lanczos resampling
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # If the resized image doesn't match 1920x1080 exactly,
            # create a new image with black borders (letterboxing/pillarboxing)
            if new_width != target_width or new_height != target_height:
                # Create new 1920x1080 image with black background
                final_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))

                # Calculate position to center the resized image
                x_offset = (target_width - new_width) // 2
                y_offset = (target_height - new_height) // 2

                # Paste resized image onto black background
                final_img.paste(img_resized, (x_offset, y_offset))
                img_resized = final_img

            # Save resized image locally with adjustable quality
            img_resized.save(local_filepath, 'JPEG', quality=95, optimize=True)

            file_size = os.path.getsize(local_filepath) / 1024  # KB
            print(f"Image captured: {filename} ({file_size:.1f}KB)")

            # Transfer to server
            remote_filepath = os.path.join(
                self.transfer_manager.remote_base_path,
                self.current_session_folder,
                filename
            )

            if self.transfer_manager.transfer_image_scp(local_filepath, remote_filepath):
                print(f"Image transferred to server: {filename}")
            else:
                print(f"Failed to transfer image: {filename}")

            return True

        except Exception as e:
            print(f"Image capture/transfer error: {e}")
            return False

    def cleanup(self):
        """Clean up camera resources"""
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
            except:
                pass


class CookingMonitorSystem:
    """Main IoT application controller"""

    def __init__(self):
        self.running = False
        self.motion_detected = False
        self.system_active = False
        self.current_session = 0

        # Initialize time manager first
        print("\nConnecting to Linux server for time synchronization...")
        self.time_manager = TimeManager(IMDB_HOST, IMDB_USER, IMDB_PASSWORD)

        # Initialize components
        self.setup_gpio()
        self.db = DatabaseManager(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, self.time_manager)
        self.c4001 = C4001Sensor()
        self.mlx90640 = MLX90640Sensor()

        # Initialize image transfer manager
        self.transfer_manager = ImageTransferManager(
            IMDB_HOST, IMDB_USER,
            self.time_manager.password,  # Reuse the password
            IMDB_FOLDER
        )

        # Initialize camera with transfer capability
        self.camera = CameraManager(IMAGE_FOLDER, self.time_manager, self.transfer_manager)

        # Threading events and queues
        self.stop_event = threading.Event()
        self.motion_queue = Queue()

        # Immediate capture flags
        self.immediate_image_flag = False
        self.immediate_thermal_flag = False

        # Motion states for sensors
        self.pir_motion = False
        self.c4001_motion = False
        self.last_pir_state = False
        self.last_c4001_state = False

        # Thermal monitoring
        self.thermal_enabled = self.mlx90640.mlx is not None
        self.last_temperature = None

        print("\nSystem initialized. Press the button to start/stop monitoring.")

    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIR_PIN, GPIO.IN)
        GPIO.setup(LED_RED_PIN, GPIO.OUT)
        GPIO.setup(LED_GREEN_PIN, GPIO.OUT)

        # Set initial LED state (green = no motion)
        GPIO.output(LED_RED_PIN, GPIO.LOW)
        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)

        # Setup button interrupt
        GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING,
                              callback=self.button_callback,
                              bouncetime=300)

        print("GPIO initialized successfully")

    def button_callback(self, channel):
        """Handle button press"""
        if not self.system_active:
            self.start_system()
        else:
            self.stop_system()

    def start_system(self):
        """Start the monitoring system"""
        if self.system_active:
            return

        print("\n" + "=" * 50)
        print("SYSTEM STARTING...")

        # Resync time at session start
        print("Resyncing time with server...")
        self.time_manager.sync_time()

        self.system_active = True
        self.running = True
        self.stop_event.clear()

        # Set LED default state
        GPIO.output(LED_RED_PIN, GPIO.LOW)
        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)

        # Increment session
        self.db.current_session += 1
        self.current_session = self.db.current_session

        # Create session folder for images
        self.camera.create_session_folder(self.current_session)

        # Record switch ON
        self.db.insert_switch(self.current_session, True)

        synced_time = self.time_manager.get_synced_time()
        print(f"Session {self.current_session} started at {synced_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Set flags for immediate capture (will be handled by threads)
        self.immediate_image_flag = True
        self.immediate_thermal_flag = self.thermal_enabled

        print("Queuing immediate captures...")
        print("Monitoring active. Press button to stop.")
        print("=" * 50 + "\n")

        # Start monitoring threads
        self.pir_thread = threading.Thread(target=self.monitor_pir)
        self.c4001_thread = threading.Thread(target=self.monitor_c4001)
        self.camera_thread = threading.Thread(target=self.camera_loop)
        self.led_thread = threading.Thread(target=self.update_led)

        # Start thermal monitoring if sensor is available
        if self.thermal_enabled:
            self.thermal_thread = threading.Thread(target=self.monitor_thermal)
            self.thermal_thread.start()

        self.pir_thread.start()
        self.c4001_thread.start()
        self.camera_thread.start()
        self.led_thread.start()

    def stop_system(self):
        """Stop the monitoring system"""
        if not self.system_active:
            return

        print("\n" + "=" * 50)
        print("SYSTEM STOPPING...")

        self.system_active = False
        self.running = False
        self.stop_event.set()

        # Record switch OFF
        self.db.insert_switch(self.current_session, False)

        # Reset switch states
        self.pir_motion = False
        self.c4001_motion = False
        self.motion_detected = False
        self.last_pir_state = False
        self.last_c4001_state = False

        # Reset LED to green
        GPIO.output(LED_RED_PIN, GPIO.LOW)
        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)

        # Clear session folder reference
        self.camera.current_session_folder = None

        print(f"Session {self.current_session} ended")
        print("System stopped. Press button to start.")
        print("=" * 50 + "\n")

    def monitor_pir(self):
        """Monitor PIR sensor in a thread"""
        while self.running:
            try:
                current_state = GPIO.input(PIR_PIN)

                if self.last_pir_state is False and current_state == GPIO.LOW:
                    self.last_pir_state = GPIO.LOW

                if current_state != self.last_pir_state:
                    self.last_pir_state = current_state
                    motion = bool(current_state)

                    # Record to database
                    self.db.insert_motion('motion1', self.current_session, motion)

                    # Update motion state
                    self.pir_motion = motion

                    synced_time = self.time_manager.get_synced_time()
                    timestamp = synced_time.strftime('%H:%M:%S')
                    if motion:
                        print(f"[{timestamp}] PIR: Motion detected")
                    else:
                        print(f"[{timestamp}] PIR: Motion ended")

                time.sleep(0.1)

            except Exception as e:
                print(f"PIR monitoring error: {e}")
                time.sleep(1)

    def monitor_c4001(self):
        """Monitor C4001 mmWave sensor in a thread"""
        while self.running:
            try:
                current_state = self.c4001.detect_motion()

                if current_state != self.last_c4001_state:
                    self.last_c4001_state = current_state

                    # Record to database
                    self.db.insert_motion('motion2', self.current_session, current_state)

                    # Update motion state
                    self.c4001_motion = current_state

                    synced_time = self.time_manager.get_synced_time()
                    timestamp = synced_time.strftime('%H:%M:%S')
                    if current_state:
                        print(f"[{timestamp}] C4001: Motion detected")
                    else:
                        print(f"[{timestamp}] C4001: Motion ended")

                time.sleep(0.1)

            except Exception as e:
                print(f"C4001 monitoring error: {e}")
                time.sleep(1)

    def monitor_thermal(self):
        """Monitor thermal camera in a thread"""
        # Wait a moment for system to initialize
        time.sleep(0.5)

        next_reading = time.time() + THERMAL_INTERVAL

        while self.running:
            try:
                # Check for immediate thermal capture flag
                if self.immediate_thermal_flag:

                    print(f"\n[Thermal] Processing immediate temperature reading...")

                    # Get temperature statistics
                    temp_stats = self.mlx90640.get_temperature_stats()

                    if temp_stats:
                        max_temp = temp_stats['max']
                        avg_temp = temp_stats['avg']

                        # Store in database
                        self.db.insert_temperature(self.current_session, max_temp)

                        # Update last temperature
                        self.last_temperature = max_temp

                        # Log to console
                        synced_time = self.time_manager.get_synced_time()
                        timestamp = synced_time.strftime('%H:%M:%S')
                        print(f"[{timestamp}] Thermal: Max={max_temp:.1f}°C, Avg={avg_temp:.1f}°C")

                    # Clear the flag
                    self.immediate_thermal_flag = False

                    # Reset next scheduled reading to maintain intervals
                    next_reading = time.time() + THERMAL_INTERVAL

                current_time = time.time()

                if current_time >= next_reading:
                    # Get temperature statistics
                    temp_stats = self.mlx90640.get_temperature_stats()

                    if temp_stats:
                        max_temp = temp_stats['max']
                        avg_temp = temp_stats['avg']

                        # Store maximum temperature in database
                        self.db.insert_temperature(self.current_session, max_temp)

                        # Update last temperature
                        self.last_temperature = max_temp

                        # Log to console
                        synced_time = self.time_manager.get_synced_time()
                        timestamp = synced_time.strftime('%H:%M:%S')
                        print(f"[{timestamp}] Thermal: Max={max_temp:.1f}°C, Avg={avg_temp:.1f}°C")

                    next_reading = current_time + THERMAL_INTERVAL

                time.sleep(1)

            except Exception as e:
                print(f"Thermal monitoring error: {e}")
                time.sleep(5)

    def update_led(self):
        """Update LED based on motion detection"""
        while self.running:
            try:
                # Motion detected if either sensor detects motion
                motion = self.pir_motion or self.c4001_motion

                if motion:
                    # Red LED for motion
                    GPIO.output(LED_RED_PIN, GPIO.HIGH)
                    GPIO.output(LED_GREEN_PIN, GPIO.LOW)

                    if not self.motion_detected:
                        self.motion_detected = True
                else:
                    # Green LED for no motion
                    GPIO.output(LED_RED_PIN, GPIO.LOW)
                    GPIO.output(LED_GREEN_PIN, GPIO.HIGH)

                    if self.motion_detected:
                        self.motion_detected = False

                time.sleep(0.05)

            except Exception as e:
                print(f"LED update error: {e}")
                time.sleep(1)

    def camera_loop(self):
        """Capture and transfer images periodically"""
        # Wait a moment for system to initialize
        time.sleep(0.5)

        next_capture = time.time() + IMAGE_INTERVAL

        while self.running:
            try:
                # Check for immediate capture flag (high priority)
                if self.immediate_image_flag:
                    print(f"\n[Camera] Processing immediate capture request...")

                    # Perform the capture
                    success = self.camera.capture_and_transfer_image(self.current_session)

                    if success:
                        print(f"[Camera] ✓ Immediate capture completed")
                    else:
                        print(f"[Camera] ✗ Immediate capture failed")
                    # Perform the capture
                    # self.camera.capture_and_transfer_image(self.current_session)

                    # Clear the flag
                    self.immediate_image_flag = False

                    # Reset next scheduled capture to maintain intervals
                    next_capture = time.time() + IMAGE_INTERVAL

                    # Display next scheduled capture time
                    # next_synced_time = self.time_manager.get_synced_time() + timedelta(seconds=IMAGE_INTERVAL)
                    # print(f"[Camera] Next scheduled capture at {next_synced_time.strftime('%H:%M:%S')}\n")

                current_time = time.time()

                if current_time >= next_capture:
                    self.camera.capture_and_transfer_image(self.current_session)
                    next_capture = current_time + IMAGE_INTERVAL

                    # Display next capture time
                    # next_synced_time = self.time_manager.get_synced_time() + timedelta(seconds=IMAGE_INTERVAL)
                    # print(f"[Camera] Next capture at {next_synced_time.strftime('%H:%M:%S')}\n")

                time.sleep(1)

            except Exception as e:
                print(f"Camera loop error: {e}")
                time.sleep(1)

    def cleanup(self):
        """Clean up all resources"""
        print("\nCleaning up resources...")

        # Stop system if running
        if self.system_active:
            self.stop_system()

        # Wait for threads to finish
        self.stop_event.set()
        time.sleep(1)

        # Clean up GPIO
        GPIO.cleanup()

        # Clean up camera
        self.camera.cleanup()

        print("Cleanup complete. Goodbye!")

    def run(self):
        """Main application loop"""
        try:
            print("\nSystem ready. Waiting for button press...")

            # Keep main thread alive
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nInterrupt received")
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    print("=" * 60)
    print("IoT HUMAN MOTION DETECTION SYSTEM")
    print("=" * 60)

    # Check if running as root (required for GPIO)
    if os.geteuid() != 0:
        print("This script must be run as root (use sudo)")
        sys.exit(1)

    # Get database credentials from command line or use defaults
    global DB_HOST, DB_PASSWORD, IMDB_HOST, IMDB_USER, IMDB_PASSWORD

    if len(sys.argv) >= 5:
        DB_HOST = sys.argv[1].strip()
        DB_PASSWORD = sys.argv[2].strip()
        IMDB_HOST = sys.argv[3].strip()
        IMDB_USER = sys.argv[4].strip()
    else:
        print("\nUsage: sudo python3 motion_detection.py [DB_HOST] [DB_PASSWORD] [IMDB_HOST] [IMDB_USER]")
        print("\nUsing configuration from file. Please update the following variables:")
        print(f"  DB_HOST: {DB_HOST}")
        print(f"  IMDB_HOST: {IMDB_HOST}")
        print(f"  IMDB_USER: {IMDB_USER}")

        # response = input("Continue with current configuration? (y/n): ")
        # if response.lower() != 'y':
        #    sys.exit(0)

    # Create and run the system
    system = CookingMonitorSystem()
    system.run()


if __name__ == "__main__":
    main()
