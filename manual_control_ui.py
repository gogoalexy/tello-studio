from tkinter import *
import threading
import datetime
import cv2
import os
import time
import platform
from pathlib import Path
from PIL import Image
from PIL import ImageTk


class ManualControlUI:
    """Wrapper class to enable the GUI."""

    def __init__(self, tello, root, outputpath):
        self.root = root
        self.tello = tello
        self.outputPath = outputpath # the path that save pictures created by clicking the takeSnapshot button 
        self.frame = None  # frame read from h264decoder and used for pose recognition 
        self.video_thread = None
        self.control_thread = None
        self.stopEvent = threading.Event()
        self.imagelabel = None

        # if the flag is TRUE,the auto-takeoff thread will stop waiting for the response from tello
        self.quit_waiting_flag = False

        # control variables
        self.stateSpeed = 0.5
        self.stateFB = 0
        self.stateLR = 0
        self.stateUD = 0
        self.stateYAW = 0

        # control flag for flip window
        self.flip_opened = False


    def _updateGUIImage(self,image):
        """
        Main operation to initialize the object of image, and update the GUI panel 
        """  
        image = ImageTk.PhotoImage(image)
        if self.imagelabel is None:
            self.imagelabel = Label(self.panel, image=image)
            self.imagelabel.image = image
            self.imagelabel.pack(side="left", padx=10, pady=10)
        else:
            self.imagelabel.configure(image=image)
            self.imagelabel.image = image

    def _videoLoop(self):
        """
        The mainloop thread of Tkinter 
        Raises:
            RuntimeError: To get around a RunTime error that Tkinter throws due to threading.
        """
        try:
            # start the thread that get GUI image and draw skeleton 
            time.sleep(0.5)
            while not self.stopEvent.is_set():                
                system = platform.system()

                # read the frame for GUI show
                self.frame = self.tello.read()
                if self.frame is None or self.frame.size == 0:
                    continue 
            
                # transfer the format from frame to image         
                image = Image.fromarray(self.frame)

                # we found compatibility problem between Tkinter,PIL and Macos,and it will 
                # sometimes result the very long preriod of the "ImageTk.PhotoImage" function,
                # so for Macos,we start a new thread to execute the _updateGUIImage function.
                if system == "Windows" or system == "Linux": 
                    self._updateGUIImage(image)
                else:
                    thread_tmp = threading.Thread(target=self._updateGUIImage,args=(image,))
                    thread_tmp.start()
                    time.sleep(0.03)                                           
        except RuntimeError as e:
            print("[INFO] caught a RuntimeError")
            
    def _controlLoop(self):
        self.tello.send_command("command")
        skipCommandCounter = 0
        while not self.stopEvent.is_set():
            time.sleep(0.05)
            if self.stateLR == 0 and self.stateFB == 0 and self.stateUD == 0 and self.stateYAW == 0:
                # Avoid sending 0,0,0,0 alot of times when not active
                if skipCommandCounter > 1:
                    continue
                self.tello.move_rc(0, 0, 0, 0)
                skipCommandCounter += 1
            else:
                self.tello.move_rc(self.stateLR, self.stateFB, self.stateUD, self.stateYAW)
                skipCommandCounter = 0

    def _setQuitWaitingFlag(self):  
        """
        set the variable as TRUE,it will stop computer waiting for response from tello  
        """       
        self.quit_waiting_flag = True        
   
    def open(self):
        """
        open the cmd window and initial all the button and text
        """     
        # Open drone connection
        self.tello.timeout = 0.3
        self.tello.connect()

        self.panel = Toplevel(self.root)
        self.panel.wm_title("Command Panel")
        self.panel.wm_protocol("WM_DELETE_WINDOW", self.onClose)

        # Lock parent window
        self.panel.grab_set()

        # btn_snapshot = Button(self.panel, text="Snapshot!",
        #                                command=self.takeSnapshot)
        # btn_snapshot.pack(side="bottom", fill="both",
        #                        expand="yes", padx=10, pady=5)

        # btn_pause = Button(self.panel, text="Pause", relief="raised", command=self.pauseVideo)
        # btn_pause.pack(side="bottom", fill="both",
        #                     expand="yes", padx=10, pady=5)

        # create text input entry
        text1 = Label(self.panel, text=
                          'W - Move Up\t\t\tArrow Up - Move Forward\n'
                          'S - Move Tello Down\t\t\tArrow Down - Move Backward\n'
                          'A - Rotate Tello Counter-Clockwise\tArrow Left - Move Left\n'
                          'D - Rotate Tello Clockwise\t\tArrow Right - Move Right\n\n'
                          'F - Take off\n'
                          'G - Land',
                          justify="left")
        text1.pack(side="top")

        btn_landing = Button(
            self.panel, text="Land", relief="raised", command=self.telloLanding)
        btn_landing.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        btn_takeoff = Button(
            self.panel, text="Takeoff", relief="raised", command=self.telloTakeOff)
        btn_takeoff.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        # binding arrow keys to drone control
        tmp_f = Frame(self.panel, width=100, height=2)
        tmp_f.bind('<KeyPress-w>', self.on_keypress_w)
        tmp_f.bind('<KeyRelease-w>', self.on_keyrelease_w)

        tmp_f.bind('<KeyPress-s>', self.on_keypress_s)
        tmp_f.bind('<KeyRelease-s>', self.on_keyrelease_s)

        tmp_f.bind('<KeyPress-a>', self.on_keypress_a)
        tmp_f.bind('<KeyRelease-a>', self.on_keyrelease_a)

        tmp_f.bind('<KeyPress-d>', self.on_keypress_d)
        tmp_f.bind('<KeyRelease-d>', self.on_keyrelease_d)

        tmp_f.bind('<KeyPress-Up>', self.on_keypress_up)
        tmp_f.bind('<KeyRelease-Up>', self.on_keyrelease_up)

        tmp_f.bind('<KeyPress-Down>', self.on_keypress_down)
        tmp_f.bind('<KeyRelease-Down>', self.on_keyrelease_down)

        tmp_f.bind('<KeyPress-Left>', self.on_keypress_left)
        tmp_f.bind('<KeyRelease-Left>', self.on_keyrelease_left)

        tmp_f.bind('<KeyPress-Right>', self.on_keypress_right)
        tmp_f.bind('<KeyRelease-Right>', self.on_keyrelease_right)

        tmp_f.bind('<KeyPress-Right>', self.on_keypress_right)
        tmp_f.bind('<KeyRelease-Right>', self.on_keyrelease_right)

        tmp_f.bind('<KeyPress-f>', self.on_keypress_f)
        tmp_f.bind('<KeyPress-g>', self.on_keypress_g)

        tmp_f.pack(side="bottom")
        tmp_f.focus_set()

        btn_flip = Button(
            self.panel, text="Flip", relief="raised", command=self.openFlipWindow)
        btn_flip.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.speed_bar = Scale(self.panel, from_=0.1, to=3.6, tickinterval=0.1, label='Speed (KPH)', 
                                resolution=0.1, command=self.updateSpeed)
        self.speed_bar.set(self.stateSpeed)
        self.speed_bar.pack(side="right")
        
        # start a thread that constantly pools the video sensor for
        # the most recently read frame
        self.video_thread = threading.Thread(target=self._videoLoop, args=())
        self.video_thread.start()

        # Start a thread, that sends controller commands to drone based on state.
        self.control_thread = threading.Thread(target=self._controlLoop, args=())
        self.control_thread.start()





    def openFlipWindow(self):
        """
        open the flip window and initial all the button and text
        """

        # check if window is already opened
        if self.flip_opened == True:
            print("[INFO] Flip window is already opened!")
            return
        else:
            panel = Toplevel(self.root)
            panel.wm_title("Gesture Recognition")

            def on_closing():
                print("[INFO] Closing flip window")
                panel.destroy()
                self.flip_opened = False

            self.btn_flipl = Button(
                panel, text="Flip Left", relief="raised", command=self.telloFlip_l)
            self.btn_flipl.pack(side="bottom", fill="both",
                                expand="yes", padx=10, pady=5)

            self.btn_flipr = Button(
                panel, text="Flip Right", relief="raised", command=self.telloFlip_r)
            self.btn_flipr.pack(side="bottom", fill="both",
                                expand="yes", padx=10, pady=5)

            self.btn_flipf = Button(
                panel, text="Flip Forward", relief="raised", command=self.telloFlip_f)
            self.btn_flipf.pack(side="bottom", fill="both",
                                expand="yes", padx=10, pady=5)

            self.btn_flipb = Button(
                panel, text="Flip Backward", relief="raised", command=self.telloFlip_b)
            self.btn_flipb.pack(side="bottom", fill="both",
                                expand="yes", padx=10, pady=5)

            self.flip_opened = True

            panel.protocol("WM_DELETE_WINDOW", on_closing)

       
    def takeSnapshot(self):
        """
        save the current frame of the video as a jpg file and put it into outputpath
        """

        # grab the current timestamp and use it to construct the filename
        ts = datetime.datetime.now()
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))

        p = os.path.sep.join((self.outputPath, filename))

        # save the file
        cv2.imwrite(p, cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR))
        print(("[INFO] saved {}".format(filename)))


    def pauseVideo(self):
        """
        Toggle the freeze/unfreze of video
        """
        if self.btn_pause.config('relief')[-1] == 'sunken':
            self.btn_pause.config(relief="raised")
            self.tello.video_freeze(False)
        else:
            self.btn_pause.config(relief="sunken")
            self.tello.video_freeze(True)

    def telloTakeOff(self):
        return self.tello.takeoff()

    def telloLanding(self):
        return self.tello.land()

    def telloFlip_l(self):
        return self.tello.flip('l')

    def telloFlip_r(self):
        return self.tello.flip('r')

    def telloFlip_f(self):
        return self.tello.flip('f')

    def telloFlip_b(self):
        return self.tello.flip('b')

    def updateSpeed(self, event):
        # Send command to drone to change flying speed
        speed = self.speed_bar.get()
        self.stateSpeed = speed
        print('reset speed to %d' % speed)

        # Convert KM/h to CM/s
        speed = int(round(speed * 27.7778))
        self.tello.set_speed(speed)

    def on_keypress_w(self, event):
        self.stateUD = 100

    def on_keyrelease_w(self, event):
        self.stateUD = 0

    def on_keypress_s(self, event):
        self.stateUD = -100
    
    def on_keyrelease_s(self, event):
        self.stateUD = 0

    def on_keypress_a(self, event):
        self.stateYAW = -100
    
    def on_keyrelease_a(self, event):
        self.stateYAW = 0

    def on_keypress_d(self, event):
        self.stateYAW = 100
    
    def on_keyrelease_d(self, event):
        self.stateYAW = 0

    def on_keypress_up(self, event):
        self.stateFB = 100
    
    def on_keyrelease_up(self, event):
        self.stateFB = 0

    def on_keypress_down(self, event):
        self.stateFB = -100

    def on_keyrelease_down(self, event):
        self.stateFB = 0

    def on_keypress_left(self, event):
        self.stateLR = -100

    def on_keyrelease_left(self, event):
        self.stateLR = 0

    def on_keypress_right(self, event):
        self.stateLR = 100

    def on_keyrelease_right(self, event):
        self.stateLR = 0

    def on_keypress_f(self, event):
        print('taking off')
        self.telloTakeOff()

    def on_keypress_g(self, event):
        self.telloLanding()

    def onClose(self):
        self.tello.disconnect()
        print("[INFO] closing manual control UI...")
        self.stopEvent.set()
        self.panel.destroy()
        

