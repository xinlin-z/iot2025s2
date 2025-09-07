#!/usr/bin/env python3
"""
IoT Human Motion Detection System
Integrates multiple sensors, camera, and PostgreSQL database
Components:
- C4001 mmWave Presence Sensor (UART)
- HC-SR501 PIR sensor (GPIO18)
- Raspberry Pi Camera
- Dual-color LED (Red: GPIO27, Green: GPIO22)
- Button (GPIO17)
- PostgreSQL database
"""

import RPi.GPIO as GPIO
import time
import threading
import os
import sys
import psycopg as pg
import subprocess
import shlex
from datetime import datetime
from picamera2 import Picamera2
from queue import Queue
import signal

# Add DFRobot library path
sys.path.append("../")
from DFRobot_C4001 import *

# GPIO Pin Configuration
BUTTON_PIN = 17
PIR_PIN = 18
LED_RED_PIN = 27
LED_GREEN_PIN = 22

# Database Configuration
DB_HOST = 'localhost'  # Change this to your PostgreSQL server
DB_PORT = '5432'
DB_NAME = 'iotdb'
DB_USER = 'iotproj'
DB_PASSWORD = 'your_password'  # Change this to your password

# Camera Configuration
IMAGE_FOLDER = "motion_images"
IMAGE_INTERVAL = 120  # 2 minutes in seconds


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""

    def __init__(self, host, port, dbname, user, password):
        self.conn_str = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
        self.current_session = 0
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
                            value BOOLEAN
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
                    cur.execute(
                        f"INSERT INTO {table_name} (session, datetime, value) VALUES (%s, %s, %s)",
                        (session, datetime.now(), value)
                    )
            return True
        except Exception as e:
            print(f"Database insert error: {e}")
            return False

    def insert_switch(self, session, value):
        """Insert switch state data"""
        #return self.insert_motion('switch', session, value)
        try:
            with pg.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {'switch'} (session, datetime, status) VALUES (%s, %s, %s)",
                        (session, datetime.now(), value)
                    )
            return True
        except Exception as e:
            print(f"Database insert error: {e}")
            return False


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

    def __init__(self, save_folder=IMAGE_FOLDER):
        self.save_folder = save_folder
        self.camera = None
        self.setup_folder()
        self.setup_camera()

    def setup_folder(self):
        """Create save folder if it doesn't exist"""
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
            print(f"Created image folder: {self.save_folder}")

    def setup_camera(self):
        """Initialize camera"""
        try:
            self.camera = Picamera2()
            config = self.camera.create_still_configuration(
                main={"size": (1920, 1080)}  # Full HD
            )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(2)  # Camera warm-up
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Camera initialization error: {e}")

    def capture_image(self, session_id):
        """Capture and save an image"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session_id}_{timestamp}.jpg"
            filepath = os.path.join(self.save_folder, filename)

            self.camera.capture_file(filepath)
            print(f"Image captured: {filename}")
            return True
        except Exception as e:
            print(f"Image capture error: {e}")
            return False

    def cleanup(self):
        """Clean up camera resources"""
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
            except:
                pass


class MotionDetectionSystem:
    """Main IoT application controller"""

    def __init__(self):
        self.running = False
        self.motion_detected = False
        self.system_active = False
        self.current_session = 0

        # Initialize components
        self.setup_gpio()
        self.db = DatabaseManager(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
        self.c4001 = C4001Sensor()
        self.camera = CameraManager()

        # Threading events and queues
        self.stop_event = threading.Event()
        self.motion_queue = Queue()

        # Motion states for both sensors
        self.pir_motion = False
        self.c4001_motion = False
        self.last_pir_state = False
        self.last_c4001_state = False

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

        self.system_active = True
        self.running = True
        self.stop_event.clear()

        # Increment session
        self.db.current_session += 1
        self.current_session = self.db.current_session

        # Record switch ON
        self.db.insert_switch(self.current_session, True)

        print(f"Session {self.current_session} started")
        print("Monitoring active. Press button to stop.")
        print("=" * 50 + "\n")

        # Start monitoring threads
        self.pir_thread = threading.Thread(target=self.monitor_pir)
        self.c4001_thread = threading.Thread(target=self.monitor_c4001)
        self.camera_thread = threading.Thread(target=self.camera_loop)
        self.led_thread = threading.Thread(target=self.update_led)

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

        # Reset LED to green
        GPIO.output(LED_RED_PIN, GPIO.LOW)
        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)

        print(f"Session {self.current_session} ended")
        print("System stopped. Press button to start.")
        print("=" * 50 + "\n")

    def monitor_pir(self):
        """Monitor PIR sensor in a thread"""
        while self.running:
            try:
                current_state = GPIO.input(PIR_PIN)

                if current_state != self.last_pir_state:
                    self.last_pir_state = current_state
                    motion = bool(current_state)

                    # Record to database
                    self.db.insert_motion('motion1', self.current_session, motion)

                    # Update motion state
                    self.pir_motion = motion

                    timestamp = datetime.now().strftime('%H:%M:%S')
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

                    timestamp = datetime.now().strftime('%H:%M:%S')
                    if current_state:
                        print(f"[{timestamp}] C4001: Motion detected")
                    else:
                        print(f"[{timestamp}] C4001: Motion ended")

                time.sleep(0.1)

            except Exception as e:
                print(f"C4001 monitoring error: {e}")
                time.sleep(1)

    def update_led(self):
        """Update LED based on motion detection"""
        while self.running:
            try:
                # Motion detected if either sensor detects motion
                motion = self.pir_motion or self.c4001_motion

                if motion != self.motion_detected:
                    self.motion_detected = motion

                    if motion:
                        # Red LED for motion
                        GPIO.output(LED_RED_PIN, GPIO.HIGH)
                        GPIO.output(LED_GREEN_PIN, GPIO.LOW)
                    else:
                        # Green LED for no motion
                        GPIO.output(LED_RED_PIN, GPIO.LOW)
                        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)

                time.sleep(0.1)

            except Exception as e:
                print(f"LED update error: {e}")
                time.sleep(1)

    def camera_loop(self):
        """Capture images periodically"""
        next_capture = time.time() + IMAGE_INTERVAL

        while self.running:
            try:
                current_time = time.time()

                if current_time >= next_capture:
                    self.camera.capture_image(self.current_session)
                    next_capture = current_time + IMAGE_INTERVAL

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
def _cmd(cmd: str, shell: bool=False) -> tuple[int,bytes,bytes]:
    """ execute a command w/ or w/o shell,
        return returncode, stdout, stderr """
    p = subprocess.run(cmd if shell else shlex.split(cmd),
                       shell=shell,
                       capture_output=True)
    return p.returncode, p.stdout, p.stderr
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
    global DB_HOST, DB_PASSWORD

    if len(sys.argv) >= 3:
        DB_HOST = sys.argv[1].strip()
        DB_PASSWORD = sys.argv[2].strip()
    else:
        print("\nUsage: sudo python3 motion_detection.py [DB_HOST] [DB_PASSWORD]")
        print("Using default localhost and password")
        response = input("Continue with defaults? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

    # Create and run the system
    system = MotionDetectionSystem()
    system.run()


if __name__ == "__main__":
    main()