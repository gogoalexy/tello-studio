import time
from PIL import Image


class TelloScript():

    def main(self, tello):
        tello.command_timeout = 5.0

        # Set speed to 50 cm/s
        tello.set_speed(50)

        # Takeoff
        tello.takeoff(delay=3)

        # Fly forward for 2m
        tello.move_forward(200)

        # Ascend a bit
        tello.move_up(100)

        # Rotate counter clockwise
        tello.rotate_ccw(180, delay=3)

        frame = tello.read()
        image = Image.fromarray(frame)
        image.show()

        # Fly forward for 2m again
        tello.move_forward(200)

        # Land
        tello.land()



