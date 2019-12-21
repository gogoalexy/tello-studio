
from tkinter import *
from tkinter import filedialog
import threading
import datetime
import cv2
import os
import time
import platform
from pathlib import Path


class ManualControlUI:
    """Wrapper class to enable the GUI."""

    def __init__(self, tello, root, outputpath):
        self.root = root
        self.tello = tello
        self.outputPath = outputpath # the path that save pictures created by clicking the takeSnapshot button 
        self.frame = None  # frame read from h264decoder and used for pose recognition 
        self.thread = None # thread of the Tkinter mainloop
        self.stopEvent = threading.Event()

        # if the flag is TRUE,the auto-takeoff thread will stop waiting for the response from tello
        self.quit_waiting_flag = False

        # control variables
        self.distance = 0.1  # default distance for 'move' cmd
        self.degree = 30  # default degree for 'cw' or 'ccw' cmd


    def _updateGUIImage(self,image):
        """
        Main operation to initialize the object of image, and update the GUI panel 
        """  
        image = ImageTk.PhotoImage(image)
        if self.panel is None:
            self.panel = Label(image=image)
            self.panel.image = image
            self.panel.pack(side="left", padx=10, pady=10)
        else:
            self.panel.configure(image=image)
            self.panel.image = image

    def videoLoop(self):
        """
        The mainloop thread of Tkinter 
        Raises:
            RuntimeError: To get around a RunTime error that Tkinter throws due to threading.
        """
        try:
            # start the thread that get GUI image and drwa skeleton 
            time.sleep(0.5)
            #self.sending_command_thread.start()
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
            
    def _sendingCommand(self):
        """
        start a while loop that sends 'command' to tello every 5 second
        """    
        while not self.stopEvent.is_set():                
            self.tello.send_command('command')        
            time.sleep(5)

    def _setQuitWaitingFlag(self):  
        """
        set the variable as TRUE,it will stop computer waiting for response from tello  
        """       
        self.quit_waiting_flag = True        
   
    def open(self):
        """
        open the cmd window and initial all the button and text
        """     
        self.panel = Toplevel(self.root)
        self.panel.wm_title("Command Panel")
        self.panel.wm_protocol("WM_DELETE_WINDOW", self.onClose)

        # Lock parent window
        self.panel.grab_set()

        btn_snapshot = Button(self.panel, text="Snapshot!",
                                       command=self.takeSnapshot)
        btn_snapshot.pack(side="bottom", fill="both",
                               expand="yes", padx=10, pady=5)

        btn_pause = Button(self.panel, text="Pause", relief="raised", command=self.pauseVideo)
        btn_pause.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        # create text input entry
        text0 = Label(self.panel,
                          text='This Controller map keyboard inputs to Tello control commands\n'
                               'Adjust the trackbar to reset distance and degree parameter',
                          font='Helvetica 10 bold'
                          )
        text0.pack(side='top')

        text1 = Label(self.panel, text=
                          'W - Move Tello Up\t\t\tArrow Up - Move Tello Forward\n'
                          'S - Move Tello Down\t\t\tArrow Down - Move Tello Backward\n'
                          'A - Rotate Tello Counter-Clockwise\tArrow Left - Move Tello Left\n'
                          'D - Rotate Tello Clockwise\t\tArrow Right - Move Tello Right',
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
        tmp_f.bind('<KeyPress-s>', self.on_keypress_s)
        tmp_f.bind('<KeyPress-a>', self.on_keypress_a)
        tmp_f.bind('<KeyPress-d>', self.on_keypress_d)
        tmp_f.bind('<KeyPress-Up>', self.on_keypress_up)
        tmp_f.bind('<KeyPress-Down>', self.on_keypress_down)
        tmp_f.bind('<KeyPress-Left>', self.on_keypress_left)
        tmp_f.bind('<KeyPress-Right>', self.on_keypress_right)
        tmp_f.pack(side="bottom")
        tmp_f.focus_set()

        btn_landing = Button(
            self.panel, text="Flip", relief="raised", command=self.openFlipWindow)
        btn_landing.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.distance_bar = Scale(self.panel, from_=0.02, to=5, tickinterval=0.01, digits=3, label='Distance(m)',
                                  resolution=0.01)
        self.distance_bar.set(0.2)
        self.distance_bar.pack(side="left")

        btn_distance = Button(self.panel, text="Reset Distance", relief="raised",
                                       command=self.updateDistancebar)
        btn_distance.pack(side="left", fill="both",
                               expand="yes", padx=10, pady=5)

        self.degree_bar = Scale(self.panel, from_=1, to=360, tickinterval=10, label='Degree')
        self.degree_bar.set(30)
        self.degree_bar.pack(side="right")

        btn_distance = Button(self.panel, text="Reset Degree", relief="raised", command=self.updateDegreebar)
        btn_distance.pack(side="right", fill="both",
                               expand="yes", padx=10, pady=5)
        
        # start a thread that constantly pools the video sensor for
        # the most recently read frame
        self.thread = threading.Thread(target=self.videoLoop, args=())
        self.thread.start()

        # TODO: do we really have to send "command" every 5 seconds?
        # the sending_command will send "command" to tello every 5 seconds
        #self.sending_command_thread = threading.Thread(target = self._sendingCommand)
        self.tello.send_command("command")



    def openFlipWindow(self):
        """
        open the flip window and initial all the button and text
        """
        
        panel = Toplevel(self.root)
        panel.wm_title("Gesture Recognition")

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

    def telloCW(self, degree):
        return self.tello.rotate_cw(degree)

    def telloCCW(self, degree):
        return self.tello.rotate_ccw(degree)

    def telloMoveForward(self, distance):
        return self.tello.move_forward(distance)

    def telloMoveBackward(self, distance):
        return self.tello.move_backward(distance)

    def telloMoveLeft(self, distance):
        return self.tello.move_left(distance)

    def telloMoveRight(self, distance):
        return self.tello.move_right(distance)

    def telloUp(self, dist):
        return self.tello.move_up(dist)

    def telloDown(self, dist):
        return self.tello.move_down(dist)

    def updateTrackBar(self):
        self.my_tello_hand.setThr(self.hand_thr_bar.get())

    def updateDistancebar(self):
        self.distance = self.distance_bar.get()
        print('reset distance to %.1f' % self.distance)

    def updateDegreebar(self):
        self.degree = self.degree_bar.get()
        print('reset distance to %d' % self.degree)

    def on_keypress_w(self, event):
        print("up %d m" % self.distance)
        self.telloUp(self.distance)

    def on_keypress_s(self, event):
        print("down %d m" % self.distance)
        self.telloDown(self.distance)

    def on_keypress_a(self, event):
        print("ccw %d degree" % self.degree)
        self.tello.rotate_ccw(self.degree)

    def on_keypress_d(self, event):
        print("cw %d m" % self.degree)
        self.tello.rotate_cw(self.degree)

    def on_keypress_up(self, event):
        print("forward %d m" % self.distance)
        self.telloMoveForward(self.distance)

    def on_keypress_down(self, event):
        print("backward %d m" % self.distance)
        self.telloMoveBackward(self.distance)

    def on_keypress_left(self, event):
        print("left %d m" % self.distance)
        self.telloMoveLeft(self.distance)

    def on_keypress_right(self, event):
        print("right %d m" % self.distance)
        self.telloMoveRight(self.distance)

    def on_keypress_enter(self, event):
        if self.frame is not None:
            self.registerFace()
        self.tmp_f.focus_set()
    
    def onClose(self):
        print("[INFO] closing manual control UI...")
        self.stopEvent.set()
        self.panel.destroy()
        

