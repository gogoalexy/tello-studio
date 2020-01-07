import time


class TelloScript():

    def main(self, tello):
        # Set speed to 50 cm/s
        tello.set_speed(50)

        # Takeoff and wait for 5 seconds
        tello.takeoff(delay=5)

        # Make a 360 degree rotation clockwise
        tello.rotate_cw(90, delay=5)

        # Fly forward for 1m
        tello.move_forward(100, delay=5)

        # Rotate 180 degrees counter clockwise
        tello.rotate_ccw(180, delay=5)

        # Fly forward for 1m again
        tello.move_forward(100, delay=5)

        # Land
        tello.land()
