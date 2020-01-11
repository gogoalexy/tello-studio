import time
from PIL import Image


class TelloScript():

    def main(self, tello):
        tello.command_timeout = 5.0

        # Set speed to 50 cm/s
        tello.set_speed(50)

        # Takeoff
        tello.takeoff(delay=3)

        start = time.time()
        while True:
            frame = tello.read()
            image = Image.fromarray(frame)
            image.show()
            time.sleep(0.5)
            now = time.time()
            if now - start > 20:
                break
        # Land
        tello.land()


