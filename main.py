import tello as tello
from tello_control_ui import TelloUI


def main():
    # Initianile drone interface
    # drone = None
    drone = tello.Tello('', 8889, imperial=False)

    # start the Tkinter mainloop
    mainUI = TelloUI(drone)
    mainUI.root.mainloop()

if __name__ == "__main__":
    main()
