import time
import pyfirmata2


class Drive:
    """Used for driving the car."""

    def __init__(self, board):
        # Define pins
        self.Motor_STBY = board.get_pin("d:3:o")   # standby pin
        self.Motor_PWMA = board.get_pin("d:5:p")   # PWM
        self.Motor_AIN_1 = board.get_pin("d:7:o")  # direction
        self.Motor_PWMB = board.get_pin("d:6:p")   # PWM
        self.Motor_BIN_1 = board.get_pin("d:8:o")  # direction

    def drive(self, direction: int, left_speed: int, right_speed: int):
        """Drive forward (1) or backward (-1) at speed 0–255."""
        if direction in (1, -1):
            self.Motor_STBY.write(1)
            self.Motor_PWMA.write(left_speed / 255)   # scale to 0–1
            self.Motor_AIN_1.write(1 if direction == 1 else 0)
            self.Motor_PWMB.write(right_speed / 255)
            self.Motor_BIN_1.write(1 if direction == 1 else 0)
        else:
            print("Invalid direction: must be 1 (forward) or -1 (backward)")

    def rotate(self, direction: int, left_speed: int, right_speed: int):
        """Rotate in place: 1 = right, -1 = left."""
        if direction in (1, -1):
            self.Motor_STBY.write(1)
            self.Motor_PWMA.write(left_speed / 255)
            self.Motor_AIN_1.write(1 if direction == 1 else 0)
            self.Motor_PWMB.write(right_speed / 255)

            # Opposite direction on second motor
            self.Motor_BIN_1.write(0 if direction == 1 else 1)
        else:
            print("Invalid direction: must be 1 (right) or -1 (left)")

    def stop(self):
        """Stop both motors."""
        self.Motor_STBY.write(0)
        self.Motor_PWMA.write(0)
        self.Motor_AIN_1.write(0)
        self.Motor_PWMB.write(0)
        self.Motor_BIN_1.write(0)


if __name__ == "__main__":
    # Initialize board
    PORT = pyfirmata2.Arduino.AUTODETECT
    board = pyfirmata2.Arduino(PORT)
    
    drive = Drive(board)

    print("Forward...")
    drive.drive(1)
    time.sleep(5)
    drive.stop()

    print("Rotate right...")
    drive.rotate(1)
    time.sleep(5)
    drive.stop()

    print("Backward...")
    drive.drive(-1)
    time.sleep(5)
    drive.stop()

    print("Rotate left...")
    drive.rotate(-1)
    time.sleep(5)
    drive.stop()
