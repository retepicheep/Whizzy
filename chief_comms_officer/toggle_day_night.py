# near top of file, add
from picamera2 import controls, Picamera2
import time
# add: mode helpers
def set_day_mode(camera):
    try:
        camera.set_controls({
            "AwbEnable": True,
            "AwbMode": controls.AwbModeEnum.Daylight,  # good baseline
            "ExposureTime": 8000,      # µs, tune for brightness
            "AnalogueGain": 1.2,       # small gain boost
            "ColourGains": (0.9, 1.2)  # (red, blue) tweak these to taste
        })
    except Exception as e:
        print("set_day_mode error:", e)

def set_night_mode(camera):
    try:
        camera.set_controls({
            "AwbEnable": False,          # fix WB instead of auto
            "ExposureTime": 30000,       # longer exposure for low light
            "AnalogueGain": 4.0,         # higher gain
            "ColourGains": (1.8, 0.8)    # boost red, cut blue → reduces purple
        })
    except Exception as e:
        print("set_night_mode error:", e)


if __name__=="__main__":
    for i in range(5):
        set_day_mode(camera)
        time.sleep(5)
        set_night_mode(camera)
        time.sleep(5)
        set_day_mode(camera)
        time.sleep(5)

