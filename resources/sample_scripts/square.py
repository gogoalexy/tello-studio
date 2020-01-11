import time


class TelloScript():

    def main(self, tello):
        tello.command_timeout = 5.0

        # Set speed to 50 cm/s
        tello.set_speed(50)

        # Takeoff
        tello.takeoff(delay=3)

        # Make rotation clockwise
        tello.rotate_cw(90)
        
        # Fly forward for 1m
        tello.move_forward(100)

        # Rotate counter clockwise
        tello.rotate_ccw(90)

        tello.move_forward(100)
        tello.rotate_ccw(90)
        tello.move_forward(100)
        tello.rotate_ccw(90)
        tello.move_forward(100)

        # Land
        tello.land()

