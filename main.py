import tello as tello
from tello_control_ui import TelloUI


def main():

    drone = tello.Tello('', 8889, imperial=False)  
    mainUI = TelloUI(drone)
    
    # start the Tkinter mainloop
    mainUI.root.mainloop()

if __name__ == "__main__":
    main()
