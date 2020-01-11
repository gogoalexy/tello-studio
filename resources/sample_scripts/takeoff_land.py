import time


class TelloScript():

    def main(self, tello):
        # Send "command" to tello to enable command mode.
        tello.send_command("command")

        # Takeoff
        tello.takeoff()

        # Stay in air for 5 seconds
        time.sleep(5)

        # Land
        tello.land()
