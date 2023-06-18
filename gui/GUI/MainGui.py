import math
import time
import tkinter as tk
from threading import Thread
from tkinter import messagebox, ttk
from tkinter.filedialog import askopenfilename
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Entry
from Logic.ConfigParser import ConfigParser

import matplotlib.backends.backend_tkagg as tkagg
import pyautogui as pg
from matplotlib import pyplot as plt

from GUI import AppWidgets, FeedbackWidgets, MainFrame
from GUI.AppWidgets import MyFrame
from GUI.Styles import MyStyle
from Logic import AppBoot, PcapLogic

import ctypes
import threading

MAX_X, MAX_Y = 1400, 800

# tabs globals
ad_new_tab_flag = False
admin_flag = False


class StartGUI(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        MyStyle()
        self.window.title(f"House-GAN++")  # title of the GUI window
        self.window.iconbitmap("house_icon-removebg-preview.ico")
        place_center(self.window, width=MAX_X, height=MAX_Y)

        self.path = ""
        self.main_window = self.window
        self.selected = tk.IntVar()
        self.vars = []
        self.btns = [ttk.Checkbutton()]
        self.num_of_rooms = 0
        self.entries = None

        self.main_frame = MainFrame.CreateMainFrame(self.main_window)
        self.ab = AppBoot.AppBoot(self.main_frame.message_label_middle)
        self.initial_program()

        # Notebooks
        self.notebook_plots = AppWidgets.MyNotebook(self.main_frame.right_frame)
        self.notebook_settings = AppWidgets.MyNotebook(self.main_frame.right_frame)

    def initial_program(self):
        # set functionalities to buttons
        self.main_frame.load_bubble_diagram_btn.configure(
            command=lambda: self.open_file(extension='*.*', dest_port=self.ab.dest_port))
        self.main_frame.stop_analyzing_btn.configure(command=self.stop_threads)
        self.main_frame.plots_radio.configure(value=1, variable=self.selected, command=self.show_selected_size,
                                              state='disabled')
        self.main_frame.settings_btn.configure(command=self.settings_button, state='disabled')
        self.main_frame.download_btn.configure(command="", state='disabled')
        self.main_frame.signin_btn.configure(command=self.signin_button)

        self.selected.set(-1)

    def stop_threads(self):
        print("thread list: ", thread_list := threading.enumerate())
        for thread in thread_list:
            if thread.name != 'MainThread' and 'pydev' not in thread.name:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, ctypes.py_object(SystemExit))
                thread.join()
        PcapLogic.stop_pcap_bool = True # Stop FeedbackWidget thread
        self.main_frame.message_label_middle.config(text="")
        print(f"thread list after remove: ", threading.enumerate())
        PcapLogic.stop_pcap_bool = False

    def open_file(self, extension, dest_port):

        def insert_to_gui_thread():
            # check if pcap_bool turned on, is so, call select_plots
            self.after_idle(self.select_plots)

        def check_pcap(callback):
            while not PcapLogic.stop_pcap_bool:
                time.sleep(3)
            callback()

        # stop previous load_pcap action
        self.stop_threads()

        self.selected.set(-1)
        title = "Please choose " + extension + " file to work with"
        self.path = askopenfilename(filetypes=[("Custom Files:", extension)], title=title)
        self.main_frame.path_label_middle.configure(text="You selected "+self.path)
        if not self.path:
            print(f"Error opening file {self.path}")
            return
        extension = self.path.split('.')[1]

        # clear graphs and notebooks data
        self.notebook_plots = self.notebook_plots.destroy()
        self.notebook_plots = AppWidgets.MyNotebook(self.main_frame.right_frame)

        if extension == "pcapng" or extension == "pcap":
            t = PcapLogic.AsyncPcap2Bin(self.path, dest_port, self.main_frame.message_label_middle)
            FeedbackWidgets.AsyncPcap2Bin(self.main_frame.message_label_middle).start()

            thread = Thread(target=check_pcap, args=(insert_to_gui_thread,))
            thread.start()
            t.start()

        # elif extensions of images
        elif extension == "png" or extension == "jpg" or extension == "jpeg":
            
            # raise a pop up asking from the user to input the number of rooms in the picture
            self.num_of_rooms = tk.simpledialog.askinteger("Input", "How many rooms are in the bubble diagram?",
                                                        parent=self.main_window, minvalue=1, maxvalue=30)
            if self.num_of_rooms is None:
                # raise a pop up erroring for the user that he didn't input a number and go back to the main window
                messagebox.showerror(message="Please input a number")
                return
            
            # create a new window
            self.new_window = tk.Toplevel(self.main_window)
            self.new_window.iconbitmap("house_icon-removebg-preview.ico")
            # create a new frame
            self.new_frame = tk.Frame(self.new_window)
            self.new_frame.grid(row=0, column=0, sticky='nsew')
            ttk.Label(self.new_frame, text="Please initialize the refinement scheme mode if necessary").grid(row=0, columnspan=(self.num_of_rooms+4*2))

            room_numer=1
            out_i = 0
            for i in range(0,self.num_of_rooms+4,2):
                ttk.Label(self.new_frame, text="Room " + str(room_numer)).grid(row=1, column=i, sticky='w')
                ttk.Entry(self.new_frame, width=10).grid(row=1, column=i+1, sticky='w')
                room_numer+=1
                out_i = i 
            ttk.Label(self.new_frame, text="In doors").grid(row=1, column=out_i, sticky='w')
            ttk.Entry(self.new_frame, width=10).grid(row=1, column=out_i+1, sticky='w')
            ttk.Label(self.new_frame, text="Out doors").grid(row=1, column=out_i+2, sticky='w')
            ttk.Entry(self.new_frame, width=10).grid(row=1, column=out_i+3, sticky='w')
            room_numer=1
            for i in range(0,self.num_of_rooms+4,2):
                ttk.Label(self.new_frame, text="Room " + str(room_numer)).grid(row=2, column=i, sticky='w')
                ttk.Entry(self.new_frame, width=10).grid(row=2, column=i+1, sticky='w')
                room_numer+=1
                out_i = i 
            ttk.Label(self.new_frame, text="In doors").grid(row=2, column=out_i, sticky='w')
            ttk.Entry(self.new_frame, width=10).grid(row=2, column=out_i+1, sticky='w')
            ttk.Label(self.new_frame, text="Out doors").grid(row=2, column=out_i+2, sticky='w')
            ttk.Entry(self.new_frame, width=10).grid(row=2, column=out_i+3, sticky='w')
            ttk.Button(self.new_frame, text="OK", command=self.new_window.destroy, style="Blue.TButton").grid(row=3, columnspan=(self.num_of_rooms+4*2))
            
            

            t = PcapLogic.AsyncPcap2Bin(self.path, dest_port, self.main_frame.message_label_middle)
            FeedbackWidgets.AsyncPcap2Bin(self.main_frame.message_label_middle).start()

            thread = Thread(target=check_pcap, args=(insert_to_gui_thread,))
            thread.start()
            t.start()

        else:
            messagebox.showerror(message="Please choode pcap files or bin files")
            return

    def show_selected_size(self):
        if self.selected.get() == 1:
            self.select_plots()

    def select_plots(self):
        global ad_new_tab_flag

        self.selected.set(1)
        self.notebook_settings.grid_remove()

        if self.notebook_plots.counter == 0:
            # data = PcapLogic.deciphered_bin_df
            # stay_names = AppBoot.sites_dict.get('sites').split(':')

            # show columns of stay_names
            # remove = data.drop(columns=data.columns.difference(other=stay_names), axis=1, inplace=False)
            # length = math.ceil(len(stay_names) / 20)  # round up

            for i in range(0, self.num_of_rooms+1):
                frame = MyFrame(self.notebook_plots)

                self.notebook_plots.tabs.append(frame)

                if i is 0:
                    self.notebook_plots.add(frame, text="All")    
                else:
                    self.notebook_plots.add(frame, text="Room " + str(i))

                # pick_sites_label = ttk.Label(frame, style="Settings.TLabel", text=pick_sites_text, font=("Helvetica", 12))
                text = ttk.Label(frame, style="Settings.TLabel", text="Your floorplan here", font=("Helvetica", 32))
                text.grid(row=0, column=1, sticky="nswe")

                # fig, ax = plt.subplots()
                # fig = plt.text(0.5, 0.5, "Your floorplan here", horizontalalignment='center', verticalalignment='center',)
                # canvas = tkagg.FigureCanvasTkAgg(fig, master=frame)
                # canvas.get_tk_widget().grid(row=0, column=0, sticky="nswe")
                # canvas.get_tk_widget().grid_columnconfigure(0, weight=1)
                # toolbar = tkagg.NavigationToolbar2Tk(canvas, frame, pack_toolbar=False)
                # toolbar.update()
                # toolbar.grid(row=1, column=0)
                # y = remove.iloc[:1].values[0]
                # plt.barh((remove.columns.values[20 * i:20 * i + 20]), y[20 * i:20 * i + 20], color="#73B8FA",
                #          edgecolor="#73B8FA")

                self.notebook_plots.counter += 1

        self.main_frame.plots_radio['state'] = 'normal'
        self.main_frame.download_btn['state'] = 'normal'
        self.main_frame.settings_btn['state'] = 'normal'
        self.notebook_plots.grid(row=0, column=0, sticky="nswe")
        ad_new_tab_flag = False

    def settings_button(self):
        self.selected.set(-1)
        self.notebook_plots.grid_remove()

        if self.notebook_settings.counter == 0:
            self.create_sites_tab()  # tab[0]
            self.create_settings_tab()  # tab[1]
        self.notebook_settings.grid(row=0, column=0, sticky="nswe")

    def signin_button(self):
        self.selected.set(-1)

        # create pop up window of sign in
        self.signin_window = tk.Toplevel(self.main_window)
        self.signin_window.title("Sign in")
        # self.signin_window.geometry("350x200")
        self.signin_window.resizable(False, False)

        # create a frame for the sign in window
        self.signin_frame = ttk.Frame(self.signin_window, style='Custom.TFrame')
        self.signin_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")  # Add some padding
        self.signin_frame.grid_columnconfigure(0, weight=1)  # Make the frame stretch when resizing
        self.signin_frame.grid_rowconfigure(0, weight=1)  # Make the frame stretch when resizing
        self.signin_frame.grid_propagate(True)  # Disable resizing the frame

        # create a label for the sign in window
        self.signin_label = ttk.Label(self.signin_frame, style="Settings.TLabel", text="Sign in", font=("Helvetica", 16))
        self.signin_label.grid(row=0, column=0, columnspan=2, padx=(20,20), pady=(20,20))  # Let it span 2 columns and align to left

        # create a label for the username
        self.username_label = ttk.Label(self.signin_frame, style="Settings.TLabel", text="Username", font=("Helvetica", 12))
        self.username_label.grid(row=1, column=0, sticky="w", padx=(20,20), pady=(0,0))  # Align to left

        # create a label for the password
        self.password_label = ttk.Label(self.signin_frame, style="Settings.TLabel", text="Password", font=("Helvetica", 12))
        self.password_label.grid(row=2, column=0, sticky="w", padx=(20,20), pady=(0,20))  # Align to left

        # create a entry for the username
        self.username_entry = ttk.Entry(self.signin_frame, style="Settings.TEntry", font=("Helvetica", 12))
        self.username_entry.grid(row=1, column=1, sticky="e", padx=(0,20), pady=(0,0))  # Align to right

        # create a entry for the password
        self.password_entry = ttk.Entry(self.signin_frame, style="Settings.TEntry", font=("Helvetica", 12))
        self.password_entry.grid(row=2, column=1, sticky="e", padx=(0,20), pady=(0,20))  # Align to right

        # create a button for the sign in
        self.login_btn = ttk.Button(self.signin_frame, style="Blue.TButton", text="Login", command=self.login)
        self.login_btn.grid(row=3, column=0, columnspan=2, padx=(20,20), pady=(0,20))  # Let it span 2 columns and align to right
        
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == "admin" and password == "admin":
            self.signin_window.destroy()
            self.main_frame.settings_btn['state'] = 'normal'
            self.main_frame.download_btn['state'] = 'normal'
            self.main_frame.plots_radio['state'] = 'normal'
            self.main_frame.signin_btn['style'] = 'Green.TButton'
            self.add_train_model_button()
        else:
            messagebox.showerror("Error", "Wrong username or password")

    def add_train_model_button(self):
        self.main_frame.train_model_btn.grid(row=6, column=0, padx=5, pady=5)


    def create_sites_tab(self):
        frame = MyFrame(self.notebook_settings)
        frame.grid(row=0, column=0, sticky="nswe")

        self.notebook_settings.tabs.append(frame)
        self.notebook_settings.add(frame, text='Sites')
        self.notebook_settings.counter += 1

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=30)

        pick_sites_text = "Choose sites to present on graph:"
        pick_sites_label = ttk.Label(frame, style="Settings.TLabel", text=pick_sites_text, font=("Helvetica", 12))
        pick_sites_label.grid(row=0, column=0, sticky="w")

        bottom_frame = ttk.Frame(frame, style='Custom.TFrame')
        bottom_frame.grid(row=2, column=0, sticky="we")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(2, weight=1)

        left_bottom_frame = ttk.Frame(bottom_frame, style='Custom.TFrame')
        left_bottom_frame.grid(row=0, column=0, sticky="nswe")
        left_bottom_frame.grid_rowconfigure(0, weight=1)
        select_all_btn = ttk.Button(left_bottom_frame, style='Blue.TButton', text="select all",
                                    command=self.select_all)
        select_all_btn.grid(row=0, column=0)
        deselect_all_btn = ttk.Button(left_bottom_frame, style='Blue.TButton', text="deselect all",
                                      command=self.deselect_all)
        deselect_all_btn.grid(row=0, column=1)

        middle_bottom_frame = ttk.Frame(bottom_frame, style='Custom.TFrame')
        middle_bottom_frame.grid(row=0, column=1, sticky="nswe")
        middle_bottom_frame.grid_columnconfigure(0, weight=1)
        search_label = ttk.Label(middle_bottom_frame, style="Settings.TLabel", text='Search')
        search_label.grid(row=0, column=0)
        search_entry = Entry(middle_bottom_frame)
        search_entry.grid(row=1, column=0)

        scrolled_text = ScrolledText(frame, width=20, height=10, relief="flat")
        scrolled_text.grid(row=1, column=0, sticky="nwse")

        sites = AppBoot.sites_dict.get('sites').split(':')

        btn = ttk.Checkbutton
        i = 0
        for site in PcapLogic.deciphered_bin_df.columns:
            # create widgets
            self.btns.append(btn := ttk.Checkbutton(scrolled_text, text=site, style="Custom.TCheckbutton"))
            if site in sites:
                btn.state(['selected'])

            btn.configure(command=lambda b=btn, site_name=site: self.update_select_plots(site_name, b.state()))

            btn.grid(row=i, column=0, sticky="w")
            scrolled_text.window_create('end', window=btn)
            scrolled_text.insert('end', '\n')
            i += 1

        def get(event):
            to_search = search_entry.get()
            if to_search:
                for check_btn in self.btns:
                    if to_search == check_btn.cget("text"):
                        scrolled_text.tag_add('found', check_btn, check_btn)
                        scrolled_text.see(check_btn)
                        check_btn.configure(style='Selected.TCheckbutton')
                        check_btn.state(['selected'])
                    elif to_search in check_btn.cget("text"):
                        scrolled_text.tag_add('found', check_btn, check_btn)
                        scrolled_text.see(check_btn)
                        check_btn.configure(style='Selected.TCheckbutton')
                    else:
                        check_btn.configure(style='Custom.TCheckbutton')

        search_entry.bind("<Return>", get)
        self.notebook_settings.update()

    def select_all(self):
        for btn in self.btns:
            btn.state(['selected'])
            AppBoot.add_new_param_to_ini(btn.cget("text"), btn.cget("state"))
        self.notebook_plots = self.notebook_plots.destroy()
        self.notebook_plots = AppWidgets.MyNotebook(self.main_frame.right_frame)

    def deselect_all(self):
        for btn in self.btns:
            btn.state(['!selected'])
            AppBoot.add_new_param_to_ini(btn.cget("text"), btn.cget("state"))
        self.notebook_plots = self.notebook_plots.destroy()
        self.notebook_plots = AppWidgets.MyNotebook(self.main_frame.right_frame)

    def update_select_plots(self, site_name, btn_state):
        AppBoot.add_new_param_to_ini(site_name, btn_state)
        self.notebook_plots = self.notebook_plots.destroy()
        self.notebook_plots = AppWidgets.MyNotebook(self.main_frame.right_frame)

    def save_settings(self):
        # self.ab.dest_ip = self.ip_entry.get()
        self.ab.dest_port = self.port_entry.get()
        ConfigParser.change_settings("destination port", str(self.ab.dest_port))

    def create_settings_tab(self):
        self.notebook_settings.tabs.append(frame := tk.Frame(self.notebook_settings, bg='white'))  # tab[1]
        self.notebook_settings.add(frame, text='SETTINGS')
        self.notebook_settings.counter += 1

        font = ("Helvetica", 12)
        ttk.Label(frame, style='Settings.TLabel', text='Destination IP = ', font=font).grid(row=0, column=0,
                                                                                            sticky="e")
        ttk.Label(frame, style='Settings.TLabel', text='Destination Port = ', font=font).grid(row=1, column=0,
                                                                                              sticky="e")
        ttk.Button(frame, style='Blue.TButton', text='Save', command=self.save_settings).grid(row=2, column=0,
                                                                                                sticky="e")
        
        width = 100
        self.port_entry = ttk.Entry(frame, width=width)
        self.port_entry.grid(row=0, column=1)
        self.port_entry.insert(0, self.ab.dest_port)


def place_center(w1, width, height):  # Placing the window in the center of the screen
    reso = pg.size()
    rx = reso[0]
    ry = reso[1]
    x = int((rx / 2) - (MAX_X / 2))
    y = int((ry / 2) - (MAX_Y / 2))
    width_str = str(width)
    height_str = str(height)
    w1.geometry(width_str + "x" + height_str + "+" + str(x) + "+" + str(y))