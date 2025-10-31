import serial
import time
import sys
from flask import Flask, request, render_template, Response

sys.path.append("/usr/lib/python3/dist-packages")
from picamera2 import Picamera2
from webserver.toggle_day_night import set_day_mode, set_night_mode
from arduino_interface.interface import Drive
import pyfirmata2
import cv2
import subprocess
import psutil

app = Flask(__name__)

# ------------------ Camera Setup ------------------
camera = Picamera2()
camera.configure(camera.create_preview_configuration())
camera.start()

# ------------------ Arduino Setup ------------------
PORT = pyfirmata2.Arduino.AUTODETECT
board = pyfirmata2.Arduino(PORT)
driver = Drive(board)
speed = 150
actul_speed = 0


# ------------------ System Health Functions ------------------
def get_cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp_milli = int(f.read().strip())
    return temp_milli / 1000


def get_cpu_load():
    return psutil.cpu_percent(interval=0.5)


def get_wifi_strength():
    command = "iwconfig"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    for line in output.split(b"\n"):
        if b"Signal level" in line:
            # Extract dBm
            strength_dbm = int(line.split(b"=")[2].split(b" ")[0])

            # Convert to percentage (clamped between 0–100)
            # More realistic mapping: -100 dBm = 0%, -50 dBm = 100%
            strength_percent = f"{max(0, min(100, 2 * (strength_dbm + 100)))}%"

            # Assign a word rating
            if strength_dbm >= -50:
                quality = "Excellent"
            elif strength_dbm >= -60:
                quality = "Good"
            elif strength_dbm >= -70:
                quality = "Fair"
            elif strength_dbm >= -80:
                quality = "Weak"
            else:
                quality = "Very Poor"

            return f"{strength_dbm}, {strength_percent}, {quality}"


def send_commands(cmds: list):
    """
    Interprets a list of command strings to control the car.

    Args:
        cmds: List of strings representing active control inputs.
        Valid commands: 'w' (forward), 's' (backward), 'a' (rotate right),
        'd' (rotate left), 'space' (slow mode), 'shift' (boost mode),
        'stop drive', 'stop rotate', 'stop'
    """
    # Determine speed based on modifiers
    if "space" in cmds:
        speed = 100  # slow mode
    elif "shift" in cmds:
        speed = 200  # boost mode
    else:
        speed = 150  # default speed

    # Check for stop commands
    if "stop" in cmds or ("stop drive" in cmds and "stop rotate" in cmds):
        driver.stop()

    # Handle driving (forward/backward)
    if "stop drive" not in cmds:
        if "w" in cmds:  # Forward
            if "d" in cmds:  # Forward + right arc
                driver.drive(1, speed // 2, speed)
            elif "a" in cmds:  # Forward + left arc
                driver.drive(1, speed, speed // 2)
            else:  # Straight forward
                driver.drive(1, speed, speed)
        elif "s" in cmds:  # Backward
            if "d" in cmds:  # Backward + right arc
                driver.drive(-1, speed // 2, speed)
            elif "a" in cmds:  # Backward + left arc
                driver.drive(-1, speed, speed // 2)
            else:  # Straight backward
                driver.drive(-1, speed, speed)

    # Handle rotation (when not moving forward/backward)
    if "stop rotate" not in cmds and "w" not in cmds and "s" not in cmds:
        if "a" in cmds:  # Rotate right
            driver.rotate(1, speed, speed)
        elif "d" in cmds:  # Rotate left
            driver.rotate(-1, speed, speed)


# ------------------ Video Stream ------------------
def generate_frames():
    """Yield camera frames as multipart JPEG stream."""
    while True:
        # set_day_mode(camera)  # optional
        frame = camera.capture_array()
        _, buffer = cv2.imencode(".jpg", frame)
        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


# ------------------ Flask Routes ------------------
@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")


@app.route("/control", methods=["GET", "POST"])
def control():
    if request.method == "POST":
        data = request.get_json()
        cmds = data.get("command")
        send_commands(cmds)
        return "", 204  # keep page loaded, no reload
    return render_template("control.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/speed")
def current_speed():
    return {"speed": actul_speed}


@app.route("/system_health")
def system_health():
    """Return current system stats as JSON"""
    return {
        "cpu_temp": f"{get_cpu_temp():.1f}°C",
        "cpu_load": f"{get_cpu_load():.0f}%",
        "wifi_strength": get_wifi_strength(),
    }


# ------------------ Main ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
