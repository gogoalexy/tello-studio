import time


class TelloScript():

    def main(self, tello):
        # Send "command" to tello to enable command mode.
        tello.send_command("command")

        # Takeoff and stay in air for 5s
        tello.takeoff(delay=5)

        # Land
        tello.land()
