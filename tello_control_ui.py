import itertools
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
import tello
from pathlib import Path

from manual_control_ui import ManualControlUI


class TelloUI:

    def __init__(self):
        self.drone = tello.Tello('', 8889)

        self.program_location = os.path.dirname(os.path.abspath(__file__))
        self.script_lock = threading.Lock()
        # read and apply configs
        self.initialiseConfigs()
        # set default workspace location
        # TODO: workspace var should be replaced with DEFAULT_PROJECT_LOCATION
        self.workspace = self.LAST_OPENED_PROJECT
        # initialize the root window and image panel
        self.root = Tk()
        # hide the root window for now
        self.root.withdraw()
        # open dialog for workspace selection
        self.workspaceSelection()
        self.mainUI()

    # read config files on startup and set attributes accordingly
    def initialiseConfigs(self):
        self.configdir = Path(str(Path.home()) + "/.local/share/tello-studio")
        self.settings_file = str(self.configdir) + "/settings"
        self.last_project_file = str(self.configdir) + "/lastproject"

        # if config dir doesn't exist initalise everything / if it does just read from it
        if not self.configdir.exists():
            os.mkdir(self.configdir)
            settings_file = open(self.settings_file, "w+")
            project_file = open(self.last_project_file, "w+")
            settings_file.write(str(Path.home()) + "/tello-studio")
            project_file.close()
            settings_file.close()
        else:
            settings_file = open(self.settings_file, "r")
            settings_file.close()

        self.DEFAULT_PROJECT_LOCATION = open(self.settings_file, "r").read()
        self.LAST_OPENED_PROJECT = open(self.last_project_file, "r").read()

    # update lastproject config file
    def updateLastProjectFile(self, last_project_location):
        project_file = open(self.last_project_file, "w")
        project_file.write(str(last_project_location))
        project_file.close()

        self.LAST_OPENED_PROJECT = str(last_project_location)

    # update settings config file
    def updateSettingsFile(self, default_project_location):
        project_file = open(self.settings_file, "w")
        project_file.write(str(default_project_location))
        project_file.close()

        self.DEFAULT_PROJECT_LOCATION = str(default_project_location)

    def workspaceSelection(self):
        top = Toplevel()
        top.title("Select workspace")
        top.geometry('500x300')

        msg = Message(top, text="Select an existing workspace directory or create a new one.", width=500)
        msg.pack(side=TOP)

        frame = Frame(top)
        frame.pack(fill="x", padx=10)

        tb_path = Entry(frame)
        tb_path.insert(0, self.workspace)# + "/new")
        tb_path.pack(side=LEFT, fill="x", expand="yes")

        def update():
            path = self.setWorkspaceDialog("Choose workspace directory")
            # always make sure / is the last character of a path
            if path:
                if path[:-1] != '/':
                    path += '/'
                self.workspace = path
            tb_path.delete(0, END)
            tb_path.insert(0, self.workspace + "/new")

        btn_select = Button(frame, text="...", command=lambda: update())
        btn_select.pack(side=RIGHT)

        second_frame = Frame(top)
        second_frame.pack(fill="x", padx=10)

        default_project_msg = Message(second_frame, text="Default project location is set to " + self.DEFAULT_PROJECT_LOCATION, width=500)
        default_project_msg.pack(side=LEFT)

        # update default project location
        def updateDefault():
            path = self.setWorkspaceDialog("Choose default project folder")
            if not path == '':
                self.updateSettingsFile(path)

                default_project_msg.configure(text="Default project location is set to " + self.DEFAULT_PROJECT_LOCATION)
                self.workspace = self.DEFAULT_PROJECT_LOCATION
                tb_path.delete(0, END)
                tb_path.insert(0, self.workspace + "/new")

        btn_change_default = Button(second_frame, text="Change", command=lambda: updateDefault())
        btn_change_default.pack(side=RIGHT)

        third_frame = Frame(top)
        third_frame.pack(fill="x", padx=10)

        open_recent_msg = Message(third_frame, text="Open the most recent project", width=500)
        open_recent_msg.pack(side=LEFT)


        # get name of the last opened/created project
        def getLastProjectName():
            if self.LAST_OPENED_PROJECT == "":
                return "No known projects yet"
            else:
                if Path(self.LAST_OPENED_PROJECT + "/.tsp").exists():
                    last_project_file = open(self.LAST_OPENED_PROJECT + "/.tsp", "r")
                    return last_project_file.read()
                else:
                    self.updateLastProjectFile("")
                    return "No known projects yet"
        last_project_name = getLastProjectName()
        
        last_project_label = Label(third_frame)
        last_project_label.configure(text=last_project_name)
        #last_project_label.bind("<Button-1>", command=lambda: print("yes"))
        last_project_label.pack(side=LEFT)

        # TODO: button to open last project
        #   TODO: list multiple projects

        def createOrOpenProjectDir(location, name):
            if not Path(location).is_dir():
                os.makedirs(location)
                project_file = open(location + "/.tsp", "w+")
                project_file.write(name)
                project_file.close()
            self.updateLastProjectFile(location)

        def close():
            # TODO: make this more elegant... Prompt for project name / set later?
            createOrOpenProjectDir(tb_path.get(), tb_path.get().split("/")[-1])
            sys.path.append(self.workspace)
            top.destroy()
            self.root.deiconify()

        # bind enter and escape
        top.bind("<Return>", lambda e: close())
        top.bind("<Escape>", lambda e: self.onClose())


        btn_ok = Button(top, text="OK", command=lambda: close())
        btn_ok.pack(side=BOTTOM)

    def setWorkspaceDialog(self, title_str):
        return filedialog.askdirectory(title=title_str, initialdir=str(self.workspace))


    def mainUI(self):
        # set window to full size of screen
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        # TODO: check for drone connection

        # Divided into several frames because it's easier to manage layouts this way
        f_top = Frame(self.root, bg="green")
        f_top.pack(fill=X, expand=False)

        f_main = Frame(self.root, bg="blue")
        f_main.pack(fill=BOTH, expand=True)

        f_main_left = Frame(f_main, bg="pink")
        f_main_left.pack(side=LEFT, fill=BOTH, expand=False)

        f_main_right = Frame(f_main, bg="purple")
        f_main_right.pack(side=LEFT, fill=BOTH, expand=True)

        f_main_right_top = Frame(f_main_right, height=2, padx=20)
        f_main_right_top.pack(side=TOP, fill=BOTH, expand=False)

        f_bottom = Frame(self.root, bg="red")
        f_bottom.pack(fill=X, expand=False)

        f_main_left_top = Frame(f_main_left)
        f_main_left_top.pack(side=TOP, fill=X)

        # get selected script id from listbox
        def getSelectedFileId():
            # ce je vec elem od 0
            if len(self.lb_scripts.curselection()) == 0:
                return None
            return self.lb_scripts.curselection()[0]

        def getFileIdByName(name):
            id = 0
            for s in self.scripts:
                if s == name:
                    return id
                id += 1
            return None

        # These popups are made similarly
        # - a label clarifying what to do
        # - an Entry field for supplying text data
        # - two buttons
        #
        # Each has its own method for operating with the files
        #
        # popup for creating new files
        def _popupNewFile():
            def _createFile(file):
                if file == "":
                    tl_prompt.destroy()
                if file.split(".")[-1] != "py":
                    file = file + ".py"
                Path(self.workspace + "/" + file).touch()
                self._updateScripts()
                self._updateScriptsLB()
                tl_prompt.destroy()
            # TODO: fix proportions
            tl_prompt = Toplevel(width=300, height=100)
            tl_prompt.wm_title("Create new Python file")

            label_rename = Label(tl_prompt, text="New tello Python file:")
            label_rename.pack(side=TOP, fill=X)

            text_line = Entry(tl_prompt)
            text_line.pack(side=TOP, fill=X)

            text_line.focus_set()

            f_rename = Frame(tl_prompt)

            btn_ok = Button(f_rename, text="OK", command=lambda: _createFile(text_line.get()))
            btn_ok.pack(side=LEFT, fill=X, expand=True)
            btn_cancel = Button(f_rename, text="Cancel", command=tl_prompt.destroy)
            btn_cancel.pack(side=LEFT, fill=X, expand=True)

            f_rename.pack(side=TOP, fill=X)
            tl_prompt.bind("<Return>", lambda e: _createFile(text_line.get()))
            tl_prompt.bind("<Escape>", lambda e: tl_prompt.destroy())

        # popup for renaming files
        def _popupRenameFile():
            def _renameFile(file, newname):
                os.rename(self.workspace + "/" + file, self.workspace + "/" + newname)
                self._updateScripts()
                self._updateScriptsLB()
                tl_prompt.destroy()

            file_id = getSelectedFileId()

            # TODO: fix proportions
            tl_prompt = Toplevel(width=300, height=100)
            tl_prompt.wm_title("Rename file")

            label_rename = Label(tl_prompt, text="Rename the file")
            label_rename.pack(side=TOP, fill=X)

            text_line = Entry(tl_prompt)
            text_line.insert(INSERT, str(self.scripts[file_id]))
            text_line.pack(side=TOP, fill=X)

            f_rename = Frame(tl_prompt)

            btn_ok = Button(f_rename, text="OK", command=lambda: _renameFile(self.scripts[file_id], text_line.get()))
            btn_ok.pack(side=LEFT, fill=X, expand=True)
            btn_cancel = Button(f_rename, text="Cancel", command=tl_prompt.destroy)
            btn_cancel.pack(side=LEFT, fill=X, expand=True)

            f_rename.pack(side=TOP, fill=X)

        # popup for deleting a file
        def _popupDeleteFile():
            def _deleteFile(file):
                os.remove(self.workspace + "/" + file)
                self._updateScripts()
                self._updateScriptsLB()
                tl_prompt.destroy()

            file_id = getSelectedFileId()

            # TODO: fix proportions
            tl_prompt = Toplevel(width=300, height=100)
            tl_prompt.wm_title("Delete file")

            label_delete = Label(tl_prompt, text="Are you sure you want to delete " + self.scripts[file_id] + "?")
            label_delete.pack(side=TOP, fill=X)

            f_delete = Frame(tl_prompt)

            btn_ok = Button(f_delete, text="OK", command=lambda: _deleteFile(self.scripts[file_id]))
            btn_ok.pack(side=LEFT, fill=X, expand=True)
            btn_cancel = Button(f_delete, text="Cancel", command=tl_prompt.destroy)
            btn_cancel.pack(side=LEFT, fill=X, expand=True)

            f_delete.pack(side=TOP, fill=X)

            tl_prompt.bind("<Return>", lambda e: _deleteFile(self.scripts[file_id]))
            tl_prompt.bind("<Escape>", lambda e: tl_prompt.destroy())

        # set to none when editor is emptied
        self.file_opened = None

        # TODO: make text editor tabbed lpa
        # use a list of opened files and a list of contents (Map maybe?)
        # update UI
        # save only the currently selected file
        def openFileInTextEditor():
            # clean editor
            text_editor.delete("0.0", END)

            # save full file name to class instance
            self.file_opened = self.LAST_OPENED_PROJECT + "/" + self.scripts[getSelectedFileId()]
            file = open(self.file_opened, "r")
            contents = file.read()
            text_editor.insert("0.0", contents)
            file.close()
            lineCounterLabelUpdate()
            self.lbl_opened_file_text.set(self.file_opened)

        # save the opened file if a file has been opened
        def saveOpenedFile():
            if self.file_opened:
                contents = text_editor.get("0.0", END)
                file = open(self.file_opened, "w")
                file.write(contents)
                file.close()

        self.btn_new_file = Button(f_main_left_top, relief="raised", text="New File", command=_popupNewFile)
        self.btn_new_file.pack(side=LEFT, fill=X, expand=True)

        self.btn_new_folder = Button(f_main_left_top, relief="raised", text="New Folder")
        self.btn_new_folder.pack(side=LEFT, fill=X, expand=True)

        self.lb_scripts = Listbox(f_main_left, width=35)
        self.lb_scripts.pack(side=BOTTOM, fill=BOTH, expand=True)

        self._updateScripts()
        self._updateScriptsLB()

        # file manager listbox popup contents
        lb_scripts_popup_edit = Menu(self.root, tearoff=False)
        lb_scripts_popup_edit.add_command(label="New file", command=_popupNewFile)
        lb_scripts_popup_edit.add_command(label="Rename", command=_popupRenameFile)
        lb_scripts_popup_edit.add_command(label="Open File", command=lambda: openFileInTextEditor())
        lb_scripts_popup_edit.add_separator()
        lb_scripts_popup_edit.add_command(label="Delete", command=_popupDeleteFile)

        self.lb_scripts_popup_exists = False

        # close dirtree listbox popup
        # i don't know how this shit-show works anymore so DON'T TOUCH
        # - lb_scripts_close_popup()
        # - lb_scripts_do_popup()
        # - self.lb_scripts_popup_exists
        def lb_scripts_close_popup(popup):
            if not self.lb_scripts_popup_exists:
                self.lb_scripts_popup_exists = False
                popup.grab_release()

        # popup when click on listbox
        def lb_scripts_do_popup(event, popup):
            try:
                self.lb_scripts_popup_exists = True
                popup.tk_popup(event.x_root, event.y_root, 0)
            except Exception as e:
                print(str(e))
            finally:
                lb_scripts_close_popup(popup)

        # right click open a popup in the "file manager box" on the left
        self.lb_scripts.bind("<Button-3>", lambda e: lb_scripts_do_popup(e, lb_scripts_popup_edit))

        text_editor = Text(f_main_right, font=("Monospace", 12))
        text_editor.pack(side=RIGHT, fill=BOTH, expand=True)

        self.text_editor_lines = 0
        self.lbl_line_text = StringVar()

        # line counter method and properties
        def lineCounterLabelUpdate():
            lines = text_editor.get("0.0", END).count("\n")
            if self.text_editor_lines != lines:
                newtext = ""
                for x in range(1, lines + 2):
                    newtext += str(x) + "\n"
                self.lbl_line_text.set(newtext)

        text_editor.bind("<Return>", lambda e: lineCounterLabelUpdate())
        text_editor.bind("<BackSpace>", lambda e: lineCounterLabelUpdate())
        text_editor.bind("<Delete>", lambda e: lineCounterLabelUpdate())

        # line counter
        lbl_line = Label(f_main_right, font=("Monospace", 12), width=2, anchor=NE, justify=RIGHT, textvariable=self.lbl_line_text)
        lbl_line.pack(side=RIGHT, fill=Y)
        self.lbl_line_text.set("1\n")



        self.lbl_opened_file_text = StringVar()
        self.lbl_opened_file_text.set("No opened files yet")
        lbl_opened_file = Label(f_main_right_top, height=2, anchor=W, justify=LEFT, textvariable=self.lbl_opened_file_text)
        lbl_opened_file.pack(side=TOP, fill=X)

        # TODO: why no image is displayed?
        img_control = PhotoImage(file='resources/images/control.gif')
        self.btn_manual_ctl = Button(f_top, relief="raised", text="M", command=self.openManualControlUI)
        self.btn_manual_ctl.pack(side=LEFT)

        self.btn_run = Button(f_top, relief="raised", text="Run", command=self.runSelectedScript)
        self.btn_run.pack(side=LEFT)

        # save button
        btn_save = Button(f_top, relief="raised", text="Save file", command=lambda: saveOpenedFile())
        btn_save.pack(side=LEFT)

        # get id of selected script from listbox and replace it with -1 if it's NoneType
        def vimBindGetFileId():
            id = getSelectedFileId()
            if id is None:
                return -1
            else:
                return id

        # move selection to upper file
        def vimBindFileManagerFileUp():
            id = vimBindGetFileId()
            if id > 0:
                id -= 1
            elif id == -1:
                id = 0
            self.lb_scripts.selection_clear(0, END)
            self.lb_scripts.select_set(id)

        # move selection down
        def vimBindFileManagerFileDown():
            id = vimBindGetFileId()
            if id < len(self.scripts) - 1:
                id += 1
            self.lb_scripts.selection_clear(0, END)
            self.lb_scripts.select_set(id)

        # open selected file
        def vimBindFileManagerFileOpen():
            saveOpenedFile()
            openFileInTextEditor()

        # vim bindings
        self.root.bind("<Control-j>", lambda e: vimBindFileManagerFileDown())
        self.root.bind("<Control-k>", lambda e: vimBindFileManagerFileUp())
        self.root.bind("<Control-l>", lambda e: vimBindFileManagerFileOpen())
        self.root.bind("<Control-Return>", lambda e: vimBindFileManagerFileOpen())

        self.root.bind("<Control-J>", lambda e: [vimBindFileManagerFileDown(), vimBindFileManagerFileOpen()])
        self.root.bind("<Control-K>", lambda e: [vimBindFileManagerFileUp(), vimBindFileManagerFileOpen()])

        self.root.bind("<Control-d>", lambda e: _popupDeleteFile())
        self.root.bind("<Control-N>", lambda e: _popupNewFile())

        # normie bindings
        # if user clicks anywhere else than the popup close the popup
        self.root.bind("<Button-1>", lambda e: lb_scripts_close_popup(lb_scripts_popup_edit))
        self.root.bind("<Control-s>", lambda e: saveOpenedFile())

        self.lb_scripts.bind("<Double-Button-1>", lambda e: openFileInTextEditor())

        # set a callback to handle when the window is closed
        self.root.wm_title("Tello Studio")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)


    def openManualControlUI(self):
        ui = ManualControlUI(self.drone, self.root, self.workspace + 'images/')
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
        # Create instance of valid class from imported module
        instance = module.TelloScript()

        self.drone.connect()
        instance.main(self.drone)
        self.drone.disconnect()

    def _killScript(self):
        # If thread is still active, kill it abruptly
        print("[INFO] Terminating script execution")
        if self.script_lock.locked():
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
        self.lb_scripts.delete(0, END)
        for script in self.scripts:
            self.lb_scripts.insert(END, script)

    def onClose(self):
        print("[INFO] closing...")
        self.root.quit()

