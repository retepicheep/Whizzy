# Whizzy

Whizzy is a RC car controlled remotely via a web interface. This project seeks to build out a reliable autonomous platform capable of carrying out various missions, from mapping to object delivery using computer vision and machine learning.

https://github.com/user-attachments/assets/3d68838e-caf1-4730-a2a9-93dc345b7492

## Design Considerations

As I don't have a 3d printer, I opted for getting off the shelf components for the
chassis and motors. This also helped solve a problem I was having with motor
drivers in previous prototypes. I was then able to focus more on the software.

My setup is a little unique. I took this [kit](https://us.elegoo.com/products/elegoo-smart-robot-car-kit-v-4-0?utm_source=officiallisting&utm_medium=referral&utm_id=usstore), and installed the StandardFirmata file onto the Arduino. Currently
the only things plugged into the Arduino are the motors. I then connected the
Raspberry Pi to the Arduino via USB. The Raspberry Pi serves as the master
controller and handles the web interface and sends inputs to the Arduino.

### Software

The software is currently based on the headless version of Raspberry Pi OS. It automatically starts hosting wifi on boot. Currently it is nessacary to ssh into the pi to start the web server, but I plan to automate this in the future. The web server then takes keyboard inputs from the user and sends them to the Arduino to control the motors. The camera module streams video back to the web interface for real-time viewing.

### Hardware Requirements

Here is a list of the main hardware components needed:

- Raspberry Pi 5
- Arduino Uno or compatible board
- 4 TT-130 motors
- Some form of RC car chassis (I used the chassis from the kit linked above)
- RB-Adu-171 Camera Module or compatible camera
- Sufficient power supply (battery pack) for the Raspberry Pi, Arduino, and motors
  (I am using a random power bank plugged into the Raspberry Pi and the battery
  pack from the kit to power the motors through the Arduino)

## What's Next

This project is far from complete. I plan on laying out the ground work for autonomous control in the near future.

### Planned Features

- A LiDAR sensor for creating a 2D map of the environment
- Object recognition and detection capabilities using computer vision
- Route planning for autonomous navigation

## Contributing

Please check the issues page for current needs and development opportunities.

---
