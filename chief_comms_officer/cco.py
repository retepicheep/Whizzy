import serial
import time
import sys
from flask import Flask, request, render_template, Response

sys.path.append("/usr/lib/python3/dist-packages")
from picamera2 import Picamera2
from chief_comms_officer.toggle_day_night import set_day_mode, set_night_mode
from pilot.pilot import Drive
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


def send_commands(commands):
    global speed, actul_speed

    # Process speed modifiers first
    if "space" in commands:
        speed = 100
    elif "shift" in commands:
        speed = 200
    else:
        speed = 150

    # Handle stop commands
    if "stop" in commands:
        driver.stop()
        actul_speed = 0
        return
    if "stop drive" in commands and "stop rotate" in commands:
        driver.stop()
        actul_speed = 0
        return

    # Initialize movement flags
    forward = backward = rotate_left = rotate_right = False

    # Set movement flags based on commands
    for cmd in commands:
        if cmd == "w":
            forward = True
        elif cmd == "s":
            backward = True
        elif cmd == "d":
            rotate_left = True
        elif cmd == "a":
            rotate_right = True
        elif cmd == "stop drive":
            forward = False
            backward = False
        elif cmd == "stop rotate":
            rotate_left = False
            rotate_right = False

    # Execute movement based on flags
    if forward and not backward:
        actul_speed = speed if not (rotate_left or rotate_right) else speed * 0.7
        if rotate_left:
            driver.forward_left(actul_speed)
        elif rotate_right:
            driver.forward_right(actul_speed)
        else:
            driver.forward(actul_speed)
    elif backward and not forward:
        actul_speed = -speed if not (rotate_left or rotate_right) else -speed * 0.7
        if rotate_left:
            driver.backward_left(abs(actul_speed))
        elif rotate_right:
            driver.backward_right(abs(actul_speed))
        else:
            driver.backward(abs(actul_speed))
    elif rotate_left and not rotate_right:
        driver.rotate_left(speed)
        actul_speed = speed
    elif rotate_right and not rotate_left:
        driver.rotate_right(speed)
        actul_speed = speed
    else:
        driver.stop()
        actul_speed = 0


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
