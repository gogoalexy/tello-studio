from tkinter import *
from tkinter import filedialog
import threading
import datetime
import cv2
import os
import time
import platform
import multiprocessing
import sys
from pathlib import Path

from manual_control_ui import ManualControlUI


class TelloUI:

    def __init__(self, tello):
        self.program_location = os.path.dirname(os.path.abspath(__file__))

        self.script_lock = threading.Lock()

        # set default workspace location
        # TODO: read location from tello-studio metadata and create system specific paths
        self.workspace = str(Path.home()) + "/tello-studio/"

        self.tello = tello
        # initialize the root window and image panel
        self.root = Tk()
        # hide the root window for now
        self.root.withdraw()
        # open dialog for workspace selection
        self.workspaceSelection()

        self.mainUI()


    def workspaceSelection(self):
        top = Toplevel()
        top.title("Slect workspace")
        top.geometry('500x300')

        msg = Message(top, text="Select an existing workspace directory or create a new one.", width=500)
        msg.pack()
        
        frame = Frame(top)
        frame.pack(fill="x", padx=10)

        tb_path = Entry(frame)
        tb_path.insert(0, self.workspace)
        tb_path.pack(side=LEFT, fill="x", expand="yes")
        
        def update():
            path = self.setWorkspaceDialog()
            # TODO: path needs to have "/" at the end
            if path:
                self.workspace = path
            tb_path.delete(0, END)
            tb_path.insert(0, self.workspace)

        btn_select = Button(frame, text="...", command=lambda: update())
        btn_select.pack(side=RIGHT)

        def close():
            sys.path.append(self.workspace)

            top.destroy()
            self.root.deiconify()

        btn_ok = Button(top, text="OK", command=lambda: close())
        btn_ok.pack(side=BOTTOM)
    
         
    def setWorkspaceDialog(self):
        return filedialog.askdirectory(title="Choose workspace directory",
                                                 initialdir=str(self.workspace))

    def mainUI(self):
        # set window to full size of screen
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+0+0" % (w, h))

        # TODO: check for drone connection

        f_top = Frame(self.root, bg="green")
        f_top.pack(fill=X, expand=False)

        f_main = Frame(self.root, bg="blue")
        f_main.pack(fill=BOTH, expand=True)

        f_bottom = Frame(self.root, bg="red")
        f_bottom.pack(fill=X, expand=False)

        self.lb_scripts = Listbox(f_main, width=35)
        self.lb_scripts.pack(side=LEFT, fill=Y)

        self._updateScripts()
        self._updateScriptsLB()

        text_editor = Text(f_main)
        text_editor.pack(side=RIGHT, fill=BOTH, expand=True)

        # TODO: why no image is displayed?
        img_control = PhotoImage(file='resources/images/control.gif')
        self.btn_manual_ctl = Button(f_top, relief="raised", text="M", command=self.openManualControlUI)
        self.btn_manual_ctl.pack(side=LEFT)

        self.btn_run = Button(f_top, relief="raised", text="Run", command=self.runSelectedScript)
        self.btn_run.pack(side=LEFT)

        # set a callback to handle when the window is closed
        self.root.wm_title("Tello Studio")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

    def openManualControlUI(self):
        ui = ManualControlUI(self.tello, self.root, self.workspace + 'images/')
        ui.open()

    def runSelectedScript(self):
        idx = self.lb_scripts.curselection()[0]
        f = self.scripts[idx].split(".")[0]
        print("[INFO] running script", f)
        self.btn_manual_ctl.configure(state=DISABLED)
        self.btn_run.configure(text="Stop", command=self._killScript)

        # Spawn new process in seperate thread, to wait for it finishing
        def runScript():
            self.script_process = multiprocessing.Process(target=self._execScript, args=(f,))
            self.script_lock.acquire()
            self.script_process.start()
            self.script_process.join()
            self.script_lock.release()
            self._scriptCleanup()
        thread_tmp = threading.Thread(target=lambda: runScript())
        thread_tmp.start()
    
    def _execScript(self, f):
        module = __import__(f)

        # TODO: Check module structure for validity

        # Create instance of "TelloScript" from imported module
        instance = module.TelloScript(self.tello)
        instance.main()

    def _killScript(self):
        # If thread is still active, kill it abruptly
        print("[INFO] Terminating script execution")
        if self.script_lock.locked():
            print("tiss alive")
            self.script_process.kill()

    def _scriptCleanup(self):
        print("[INFO] Script finished")
        self.btn_run.configure(text="Run", command=self.runSelectedScript)
        self.btn_manual_ctl.configure(state=ACTIVE)

    def _updateScripts(self):
        if not os.path.exists(self.workspace):
            # TODO: various safety checks
            os.makedirs(self.workspace)
            
        files = os.listdir(self.workspace)
        # list for all python files
        self.scripts = []
        # fill the list of python files
        for f in files:
            if f.split(".")[-1] == "py":
                self.scripts.append(f)


    def _updateScriptsLB(self):
        for script in self.scripts:
            self.lb_scripts.insert(END, script)

    def onClose(self):
        print("[INFO] closing...")
        del self.tello
        self.root.quit()

