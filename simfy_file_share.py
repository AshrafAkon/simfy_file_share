# Author: Ashraful Firoz
# There are some repetative code here and there.
# I will try to fix them in the next update

# important notice: files should be encrypted in client side
# no encryption is done on the server side.
# every file has a unique data_jey. thats refered as
# data_key or info_dict['data_key']

import json
import hashlib
import time
import timeit
import os
import requests
import sys
import subprocess
import math
from tkinter import filedialog
import traceback
import logging
import datetime
import queue
import logging
import signal
import time
import threading
import tkinter as tk
import pyperclip  # sudo apt-get install xclip for linux
from pathlib import Path
from tkinter.scrolledtext import ScrolledText
import psutil
import platform
from tkinter import ttk, VERTICAL, HORIZONTAL, N, S, E, W, NW, SE, SW
from config import hard_coded_url, most_working_thread
from config import wait_time_before_trying_missing_chunks_download
from config import wait_time_before_trying_failed_uploads, security_key
import random
import string
import sqlite3
from sqlite3 import Error
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad


# without a proper user agent some shared hosting
# will block the request
# user agent to be sent with every request
user_agent = """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"""


os_platform = platform.system()  # os_platform="Linux" for linux platforms
download_chunk_queue = queue.Queue()
failed_chunk_queue = queue.Queue()
upload_exists_queue = queue.Queue()

main_processing_queue = queue.Queue()
console_display_queue = queue.Queue()
active_workers = queue.Queue()


# if any of the chunk's hash doesnt match then
# it will be pushed to file_compormised_queue
file_compromised_queue = queue.Queue()


logger = logging.getLogger(__name__)

# this is to calculate chunk size in bytes
# moving from SI kilo(1000) to binary kilo(1024)
kb = 1024
mb = kb * 1024


def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def parselink(param, given_link):
    a = given_link.split("&")
    for x in a:
        if x.split("=")[0] == param:
            return x.split("=")[1]


def console_display(msg_arr):
    """this function will put the msg array to
    console dispplay queue and the queue is
    checked periodically for new messages"""
    console_display_queue.put(msg_arr)


def hashgen(data_file):
    """this function is used to create unique
    data key/security key"""
    with open(data_file, 'rb') as f:
        hash_data = f.read(2000)
    return hashlib.md5(hash_data).hexdigest()


class UploadSection:
    """This is the Upload Data section"""

    def __init__(self, frame, root, console):
        # self console prints the console data
        # declaring classwide variables
        self.console = console
        self.frame = frame
        self.filename = ""
        self.data_key = ""
        self.root = root
        self.download_exists_queue = queue.Queue()

        # we need to use global. because if we dont
        # then python's garbage collector will eat
        # this variables and we wont be able to
        # interact with them
        global photo_choose_file_button
        global select_file_button
        global photo_upload_button
        global upload_button_upload_section
        global photo_data_key_button
        global host_up_power_button_photo
        #global photo_copy_direct_link

        photo_choose_file_button = tk.PhotoImage(
            master=self.root, file='support_files/sf.png')
        select_file_button = tk.Button(frame, text="choose file", image=photo_choose_file_button,
                                       command=self.select_file, height=60, borderwidth=1,
                                       width=180)  # relief = "solid"
        select_file_button.grid(column=0, padx=10, row=0, sticky=E)

        photo_upload_button = tk.PhotoImage(
            master=self.root, file='support_files/up.png')
        upload_button_upload_section = tk.Button(frame, text="Upload", image=photo_upload_button,
                                                 command=self.upload_selected_file, height=60,
                                                 width=200, borderwidth=1)
        upload_button_upload_section.grid(column=1, row=0, pady=10, sticky=W)

        # Copy Direct Link
        # photo_copy_direct_link = tk.PhotoImage(
        #     master=self.root, file='support_files/copy_direct_link.png')
        # copy_direct_link = tk.Button(frame, text="Upload", image=photo_copy_direct_link,
        #                              command=self.copy_direct_link, height=60,
        #                              width=60, borderwidth=1)
        # copy_direct_link.grid(column=2, row=0, pady=10, sticky=W, padx=10)

        # server: label
        tk.Label(self.frame, text='Server:').grid(column=0, row=1, sticky=W)

        # host key input box. its a global variable
        self.host_entry = tk.Entry(frame, textvariable=tk.StringVar(
            frame, value=hard_coded_url), width=25)
        self.host_entry.grid(column=1, row=1, sticky=(W, E), pady=10)
        global host_entry
        host_entry = self.host_entry

        global host_down_power_button_photo
        host_up_power_button_photo = tk.PhotoImage(
            master=root, file='support_files/host_on.png')
        host_down_power_button_photo = tk.PhotoImage(
            master=root, file='support_files/host_off.png')
        self.host_power_button = tk.Button(frame, text="Turn Host On/OFF", image=host_down_power_button_photo,
                                           command=self.update_host_entry_box,
                                           height=20, width=20)
        self.host_power_button.grid(row=1, column=2)
        # host_entry should be disabled for basic.
        # set the basic host in support_files/config.txt
        self.host_entry.configure(state=tk.DISABLED)
        tk.Label(self.frame, text='Download link:').grid(
            column=0, row=2, sticky=W, pady=5)

        # data_key_box holds the file security key
        # data_key_box_str is sent to filehandler
        # filhandler assigns the security key to it

        self.data_key_box_str = tk.StringVar(frame, value='')
        self.data_key_box = tk.Entry(
            frame, width=25, textvariable=self.data_key_box_str)
        self.data_key_box.grid(column=1, row=2, sticky=(W, E))

        photo_data_key_button = tk.PhotoImage(
            master=self.root, file='support_files/cp.png')
        tk.Button(frame, text="copy file security key \nto clipboard",
                  image=photo_data_key_button,
                  command=self.copy_data_key, height=24,
                  width=24, borderwidth=1).grid(column=2, row=2, padx=10)

        # this is the styling for using %number on thep rogressbar
        self.style = ttk.Style(self.root)
        # add label in the layout
        # check out this question on stackoverfollow
        # https://stackoverflow.com/questions/58918648/displaying-percentage-in-ttk-progressbar
        self.style.layout('text.Horizontal.TProgressbar',
                          [('Horizontal.Progressbar.trough',
                            {'children': [('Horizontal.Progressbar.pbar',
                                           {'side': 'left', 'sticky': 'ns'})],
                             'sticky': 'nswe'}),
                              ('Horizontal.Progressbar.label', {'sticky': ''})])
        # set initial text
        self.style.configure('text.Horizontal.TProgressbar', text='0.00 %')

        # creating progressbar
        self.variable = tk.DoubleVar(root)
        self.pbar = ttk.Progressbar(
            self.frame, length=410, style='text.Horizontal.TProgressbar', variable=self.variable)
        self.pbar.grid(row=3, column=0, columnspan=3,
                       pady=10, padx=4, sticky=W)

        self.download_speed_var = tk.StringVar()
        self.download_speed_var.set('Upload speed: 0.00 Mbps')
        self.download_label = tk.Label(self.frame, textvariable=self.download_speed_var,
                                       width=30)
        self.download_label.grid(column=0, row=4, columnspan=3, sticky=N)
        self.download_label.configure(borderwidth=0)

        self.pid = os.getpid()
        print("pid: ", self.pid)
        # this is to get the network card to monitor network speed
        # this speed checker currenty displays the whole system's
        # network speed
        visit_ex = threading.Thread(target=self.visit_example)
        visit_ex.daemon = True
        visit_ex.start()

    def copy_direct_link(self):
        print("direct link is: ", host_entry.get() +
              "/index.html?security_key="+self.data_key_box.get())
        pyperclip.copy(host_entry.get() +
                       ":3000/download?key="+self.data_key_box.get())

    def visit_example(self):
        self.list1 = []
        self.network_card = False
        self.card_list = []
        for card in psutil.net_io_counters(pernic=True):
            self.list1.append(psutil.net_io_counters(
                self.pid)[card].bytes_sent)
            self.card_list.append(card)

        for card in psutil.net_io_counters(pernic=True):
            self.list1.append(psutil.net_io_counters(
                self.pid)[card].bytes_sent)

        try:
            requests.post("https://example.com")
            requests.post("https://example.com")
            requests.post("https://example.com")
        except Exception as e:
            print(e)

        list2 = []
        for card in psutil.net_io_counters(pernic=True):
            list2.append(psutil.net_io_counters(self.pid)[card].bytes_sent)

        for i in range(len(list2)):
            if (list2[i] - self.list1[i]) > 10:
                self.network_card = self.card_list[i]

        print(self.network_card)
        self.root.after(100, self.check_speed)

    def check_speed(self):
        x = threading.Thread(target=self.upload_download_speed_checker)
        x.daemon = True
        x.start()

    def upload_download_speed_checker(self):
        """This function checks upload speed"""
        try:
            last_time = time.time()
            last_bytes = psutil.net_io_counters(
                pernic=True)[self.network_card].bytes_sent
            while True:
                now_bytes = psutil.net_io_counters(
                    pernic=True)[self.network_card].bytes_sent
                now_time = time.time()
                down_speed = (((now_bytes - last_bytes) /
                               (now_time - last_time)) / 1000000.00)*8.00
                self.download_speed_var.set(
                    "Upload speed: {:.3f} Mbps".format(down_speed))
                last_time = now_time
                last_bytes = now_bytes
                time.sleep(1)
        except:
            self.root.after(200, self.upload_download_speed_checker)

    def update_host_entry_box(self):
        # self.host_entry.configure(state=tk.NORMAL)
        if self.host_entry['state'] == tk.NORMAL:
            self.host_entry.configure(state=tk.DISABLED)
            self.host_power_button.configure(
                image=host_down_power_button_photo)
        else:
            self.host_entry.configure(state=tk.NORMAL)
            self.host_power_button.configure(image=host_up_power_button_photo)

    def upload_progress_bar(self, a, b):
        if a == False:
            self.pbar['value'] = 0  # increment progressbar
            self.variable.set(0.00)
            self.style.configure('text.Horizontal.TProgressbar',
                                 text='{:.2f} %'.format(0.00))

        elif self.variable.get() + a/b < 100.00:
            self.pbar.step(a/b)  # increment progressbar
            self.style.configure('text.Horizontal.TProgressbar',
                                 text='{:.2f} %'.format(self.variable.get()))  # update label
        else:
            self.pbar.step(99.99-self.variable.get())
            self.style.configure('text.Horizontal.TProgressbar',
                                 text='{:.2f} %'.format(100.00))  # update label

    def copy_data_key(self):
        """function to copy the secure key in clipboard
        You need to install xclip on linux to use pyperclip"""
        if(len(self.data_key_box.get()) > 0):
            pyperclip.copy(self.data_key_box.get())

    def select_file(self):
        """function to select a file"""
        self.filename = filedialog.askopenfilename(initialdir="", title="Select file",
                                                   filetypes=(("all files", "*.*"),
                                                              ("exe files",
                                                               "*.exe"),
                                                              ("jpeg files", "*.jpg")))
        if len(self.filename) > 0:
            console_display("File selected: " +
                            self.filename.split("/")[-1])

        else:
            console_display(["No File Selected", "WARNING"])

    def upload_selected_file(self):
        if len(self.filename) != 0:
            print(self.filename)
            # logg.set("file "+root.filename + " selected")

            if len(self.host_entry.get()) < 5:
                console_display(
                    ["Please provide a valid server url", "ERROR"])
                return
            if self.host_entry.get()[-1] == "/":

                final_host = self.host_entry.get()[:-1]
            else:
                final_host = self.host_entry.get()
            console_display("Using server: " + final_host)
            self.upload_progress_bar(False, 1)
            file_upload = UploadHandler(data_file=self.filename, url=final_host,
                                        data_key_box_str=self.data_key_box_str,
                                        root=self.root, progress_bar=self.upload_progress_bar)

            # putting file_upload.splitfiles() in the main queue to execute
            main_processing_queue.put(file_upload.start_upload)
            select_file_button.configure(state=tk.DISABLED)
            upload_button_upload_section.configure(state=tk.DISABLED)

        else:
            console_display("Please choose a file before pressing upload")


class DownloadSection:
    """Class of download data section. pass
    downlaod data frame, root, console"""

    def __init__(self, frame, root, console):
        self. root = root
        self.console = console
        self.frame = frame

        tk.Label(self.frame, text='Download Link:').grid(
            column=0, row=1, sticky=W, pady=10)
        self.data_key_box_var = tk.StringVar(frame, value="")
        self.data_key_box = tk.Entry(
            frame, width=40, textvariable=self.data_key_box_var)
        self.data_key_box.grid(column=1, row=1, sticky=(W, E), padx=10)

        global photo_paste_button
        photo_paste_button = tk.PhotoImage(
            master=self.frame, file='support_files/pt.png')
        tk.Button(self.frame, text="Paste", image=photo_paste_button,
                  command=self.paste_to_data_key, height=18,
                  width=18).grid(column=2, row=1, padx=2, sticky=W)

        global photo_download_button
        photo_download_button = tk.PhotoImage(
            master=self.root, file='support_files/dn.png')
        global download_button
        download_button = tk.Button(frame, text="Download", image=photo_download_button,
                                    command=self.download_files_from_host, height=60,
                                    width=200)
        download_button.grid(column=0, row=2, padx=15,
                             pady=4, columnspan=2, sticky=W)

        global change_download_folder_photo
        change_download_folder_photo = tk.PhotoImage(
            master=self.root, file='support_files/download_folder.png')
        tk.Button(frame, text="Downloads Folder", image=change_download_folder_photo,
                  command=self.change_download_folder, height=60,
                  width=78).grid(column=1, row=2, sticky=E, padx=5)

        tk.Label(self.frame, text='Server:').grid(column=0, row=0, sticky=W)
        self.down_host_box_var = tk.StringVar(frame, value=hard_coded_url)
        self.host_entry = tk.Entry(
            frame, textvariable=self.down_host_box_var, width=40)
        self.host_entry.grid(column=1, row=0, sticky=(W, E), pady=10, padx=10)

        self.style_d = ttk.Style(self.root)
        # add label in the layout
        self.style_d.layout('text.Horizontal.TProgressbar_d',
                            [('Horizontal.Progressbar.trough',
                              {'children': [('Horizontal.Progressbar.pbar',
                                             {'side': 'left', 'sticky': 'ns'})],
                               'sticky': 'nswe'}),
                                ('Horizontal.Progressbar.label', {'sticky': ''})])
        # set initial text
        self.style_d.configure('text.Horizontal.TProgressbar_d', text='0.00 %')
        # create progressbar
        self.vari = tk.DoubleVar(self.frame)
        self.dbar = ttk.Progressbar(
            self.frame, length=370, style='text.Horizontal.TProgressbar_d', variable=self.vari)
        self.dbar.grid(row=3, column=0, columnspan=3,
                       pady=10, padx=4, sticky=SW)

        self.host_power_button = tk.Button(frame, text="Turn Host On/OFF", image=host_down_power_button_photo,
                                           command=self.update_host_entry_box,
                                           height=20, width=20)
        self.host_power_button.grid(row=0, column=2, sticky=W)
        self.host_entry.configure(state=tk.DISABLED)

        self.download_speed_var = tk.StringVar()
        self.download_speed_var.set('Download speed: 0.00 Mbps')
        self.download_label = tk.Label(self.frame, textvariable=self.download_speed_var,
                                       width=30)
        self.download_label.grid(column=0, row=4, columnspan=3, sticky=N)
        self.download_label.configure(borderwidth=0)
        # tk.Label(self.frame,text="pani" ,height =5, width =10).grid(row = 4, column =1)

        visit_ex = threading.Thread(target=self.visit_example)
        visit_ex.daemon = True
        visit_ex.start()

    def visit_example(self):
        self.list1 = []
        self.network_card = False
        self.card_list = []
        for card in psutil.net_io_counters(pernic=True):
            self.list1.append(psutil.net_io_counters(
                pernic=True)[card].bytes_sent)
            self.card_list.append(card)

        for card in psutil.net_io_counters(pernic=True):
            self.list1.append(psutil.net_io_counters(
                pernic=True)[card].bytes_sent)

        try:
            # generating some trafic so that psutil returns value greater than 10
            requests.post("https://example.com")
            requests.post("https://example.com")
            requests.post("https://example.com")
        except Exception as e:
            print(e)

        list2 = []
        for card in psutil.net_io_counters(pernic=True):
            list2.append(psutil.net_io_counters(pernic=True)[card].bytes_sent)

        for i in range(len(list2)):
            if (list2[i] - self.list1[i]) > 10:
                self.network_card = self.card_list[i]

        print(self.network_card)
        self.root.after(100, self.check_speed)

    def check_speed(self):
        x = threading.Thread(target=self.upload_download_speed_checker)
        x.daemon = True
        x.start()

    def upload_download_speed_checker(self):
        last_time = time.time()
        last_bytes = psutil.net_io_counters(
            pernic=True)[self.network_card].bytes_recv
        while True:
            now_bytes = psutil.net_io_counters(
                pernic=True)[self.network_card].bytes_recv
            now_time = time.time()
            down_speed = (((now_bytes - last_bytes) /
                           (now_time - last_time)) / 1000000.00)*8.00
            self.download_speed_var.set(
                "Download speed: {:.3f} Mbps".format(down_speed))
            last_time = now_time
            last_bytes = now_bytes
            time.sleep(1)

    def change_download_folder(self):
        path = os.path.realpath(os.path.join(Path.home(), "Downloads"))
        if os_platform == 'Windows':
            try:
                os.startfile(path)
            except Exception as e:
                print(e)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, path])

    def update_host_entry_box(self):
        # self.host_entry.configure(state=tk.NORMAL)
        if self.host_entry['state'] == tk.NORMAL:
            self.host_entry.configure(state=tk.DISABLED)
            self.host_power_button.configure(
                image=host_down_power_button_photo)
        else:
            self.host_entry.configure(state=tk.NORMAL)
            self.host_power_button.configure(image=host_up_power_button_photo)

    def paste_to_data_key(self):
        self.data_key_box_var.set(pyperclip.paste())
        # self.root.update_idletasks()
        # self.root.update()

    def download_progress_bar(self, a, b):
        if a == False:
            self.dbar['value'] = 0  # increment progressbar
            self.vari.set(0.00)
            self.style_d.configure('text.Horizontal.TProgressbar_d',
                                   text='{:.2f} %'.format(0.00))
            # self.root.update_idletasks()
            # self.root.update()

        elif self.vari.get() + a/b < 100.00:
            self.dbar.step(a/b)  # increment progressbar
            self.style_d.configure('text.Horizontal.TProgressbar_d',
                                   text='{:.2f} %'.format(self.vari.get()))  # update label
        else:
            self.dbar.step(99.99-self.vari.get())
            self.style_d.configure('text.Horizontal.TProgressbar_d',
                                   text='{:.2f} %'.format(100.00))  # update label

    def download_files_from_host(self):
        data_key = self.data_key_box.get()
        if self.host_entry.get()[-1] == "/":

            final_host = self.host_entry.get()[:-1]
        else:
            final_host = self.host_entry.get()

        if len(final_host) < 0:
            console_display(["Please provide a valid server url.", "ERROR"])
        download_button.configure(state=tk.DISABLED)

        self.download_progress_bar(False, 1)
        if(len(data_key) > 0):

            self.download_progress_bar(1, 1)
            temp_files = DownloadHandler(
                data_key=data_key, url=final_host,  root=self.root,
                progress_bar=self.download_progress_bar, download_link=self.data_key_box.get())

            # putting download_info_dict in the main
            # processing queue and getting the chain started
            main_processing_queue.put(temp_files.download_info_dict)

        else:
            download_button.configure(state=tk.NORMAL)
            print("Please provide a File Security Key first then press Download")
            console_display(
                "Please provide a File Security Key first then press Download")


class ConsoleUi:
    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, frame, root):
        self.root = root
        self.frame = frame
        self.qu_count = 0

        # moved to global queue
        # self.global_queue = console_display_queue

        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText(
            frame, state='disabled', height=5, width=107)
        self.scrolled_text.grid(
            row=1, column=0, columnspan=2, padx=10, pady=10, sticky=(N, S, W))

        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config(
            'CRITICAL', foreground='red', underline=1)
        self.scrolled_text.tag_config('SUCCESS', foreground='green')
        self.scrolled_text.tag_config('BLUE', foreground='blue')

        self.frame.after(100, self.poll_log_queue)

    def poll_log_queue(self):
        # for _ in range(len(console_display_queue)):
        # if (self.qu_count < len(console_display_queue)):
        if not console_display_queue.empty():
            msg = console_display_queue.get()
            self.scrolled_text.configure(state='normal')
            if type(msg) == type(str()):
                self.scrolled_text.insert(tk.END, str(
                    self.qu_count)+": "+msg + " " + '\n', "INFO")

            else:
                self.scrolled_text.insert(tk.END, str(
                    self.qu_count)+": "+msg[0] + " " + '\n', msg[1])  # , record.levelname)
            self.scrolled_text.configure(state='disabled')
            # Autoscroll to the bottom
            self.scrolled_text.yview(tk.END)  # scrolling view to end, IG
            self.qu_count += 1
            if not console_display_queue.empty():
                self.root.after(10, self.poll_log_queue)

        self.frame.after(100, self.poll_log_queue)

    # logger.log(lvl, self.message.get())


class DownloadHandler():
    def __init__(self, data_key="", root=None, url=hard_coded_url, progress_bar=None,
                 data_key_box_str=None, download_link=""):
        self.progress_bar = progress_bar
        self.download_link = download_link
        self.root = root
        self.data_key = parselink('id', self.download_link)
        self.key = parselink("key", self.download_link)
        self.checksum = parselink('checksum', self.download_link)
        self.url = url
        if len(self.url) > 5:
            if self.url[-1] == "/":

                self.url = self.url[-1]
            else:
                self.url = self.url

            # self.url = host_entry.get()
        else:
            console_display(["Please provide a valid server.", "ERROR"])
            upload_button_upload_section.configure(state=tk.NORMAL)
            select_file_button.configure(state=tk.NORMAL)
            return

        if os.path.isdir(os.path.join(Path.home(), "Downloads")) is False:
            os.mkdir(os.path.join(Path.home(), "Downloads"))
        if os.path.isdir(os.path.join(Path.home(), "Downloads", "downloads_data")) is False:
            os.mkdir(os.path.join(Path.home(), "Downloads", "downloads_data"))

        # this counter are used to determine how many timer certain
        # function has failed due to no inter or connection error to the server
        self.count_no_internet = 0
        self.threading_upload_count = 0
        self.download_chunk_thread_count = 0
        self.merge_files_try_count = 0
        self.missing_chunks_is_retry = False

    def download_info_dict(self):
        self.merge_files_try_count = 0
        self.missing_chunks_is_retry = False
        self.download_exists_queue = queue.Queue()
        self.progress_bar(1, 1)
        try:
            console_display("File download started")
            encrypted_info_dict = requests.post(self.url+"/process_info_dict.php",
                                                data={'security_key': security_key,
                                                      'data_key': self.data_key,
                                                      'download_info_dict': 'true'},
                                                headers={'User-Agent': user_agent}).content

            #revive_data_req = json.loads(revive_data_req)
            if len(encrypted_info_dict) == 0:
                # if len 0 that means no data is present

                console_display(
                    ["File not found for id: "
                     + self.data_key, "ERROR"]
                )
                # print("progress 710")
                self.progress_bar(False, 1)
                download_button.configure(state=tk.NORMAL)
                # self.root.update_idletasks()
                # self.root.update()
                return

            iv = encrypted_info_dict[0:16]
            key = bytes.fromhex(self.key)
            self.info_dict = json.loads(unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(
                encrypted_info_dict[16:]), AES.block_size))

            self.progress_bar(1, 1)

            #console_display("File Information Downloaded")

            logging.info("info dict downloaded")
            if(len(self.info_dict) <= 1):
                logging.error("info_dict returned empty")
                console_display("File not found on server")
                download_button.configure(state='tk.NORMAL')
                return

            # increasing progress bar 1%
            self.progress_bar(1, 1)
            console_display("Downloading Chunks")

            # populating download_chunk_queue with
            # all chunks_name. later worker process
            # will get a chunk name form this queue
            # and start downloading process
            # chunk_name is a two element list. first
            # is the name and 2nd one is sha256 hash
            # to verify chunk integrity
            for chunk_info in self.info_dict['file_serial']:
                # print(chunk_name)
                download_chunk_queue.put(chunk_info)
            finished_file_name = os.path.join(Path.home(), "Downloads",
                                              self.info_dict['file_name'])
            if os.path.isfile(finished_file_name):
                # file exists. finish_download will check if
                # the file is valid
                print("exits")
                if os.path.getsize(finished_file_name) == self.info_dict['file_size']:

                    self.progress_bar(100, 1)
                    console_display(["File Already Exists", "SUCCESS"])
                    download_button.configure(state=tk.NORMAL)
                    self.open_folder_with_file()
                    return
                else:
                    # there is a file present but the file size
                    # doesnt match. file will be downloaded and
                    # name will have 5 random letter at end
                    _file_name_list = self.info_dict['file_name'].split(".")
                    self.info_dict['file_name'] = ''.join(
                        _file_name_list[:-1]) + "_"+randomString(5) + "." + _file_name_list[-1]
                    print("file exists. new file name: ",
                          self.info_dict['file_name'])

                    # console_display(['File Download completed.', "SUCCESS"])

            main_processing_queue.put(self.download_chunks_main)

        except ConnectionError as e:
            print(e)
            if (self.count_no_internet > 30):
                console_display(
                    ["Failed to download file due to no internet, try again later.", "ERROR"])
                self.count_no_internet = 0
                return

            console_display(
                ["No internet. Cant download file information.", "ERROR"])
            self.count_no_internet += 1
            self.root.after(3000, self.download_info_dict)
        except Exception as e:
            print(e)

    def download_chunks_main(self):
        """main function that generates threads of download_chunk_thread"""

        if(os.path.isdir(os.path.join(Path.home(), "Downloads",
                                      "downloads_data",
                                      self.info_dict['data_key'])) is False):

            # checking if the directory exists to downlaod the file. if doesnt then make one
            os.mkdir(os.path.join(Path.home(), "Downloads",
                                  "downloads_data", self.info_dict['data_key']))

        if active_workers.qsize() < most_working_thread and download_chunk_queue.empty() is not True:
            # print("active workers: " + str(active_workers.qsize()))
            active_workers.put("1")
            main_processing_queue.put(self.download_chunk_thread)

        if file_compromised_queue.empty() is not True:
            # one of the chunks hash didnt match
            # file is compromised
            logging.info("aborting download. file compromised")
            return

        if download_chunk_queue.empty() is not True or active_workers.qsize() > 0:
            main_processing_queue.put(self.download_chunks_main)

        else:
            main_processing_queue.put(self.mergefiles())

    def download_chunk_thread(self):
        """this is main function that downloads
         a single chunk from server provided
         with idd(the serial number of chunk"""

        # getting a chunk name from the queue
        # chunk_info = {name, hash, key}
        # if chunk_file (the chunk) exists then we
        # are checking the size of the file
        # if its not the last chunk of the file
        # then it should have the size equal to
        # info_dict['chunk_size']

        chunk_info = download_chunk_queue.get()
        chunk_file = os.path.join(
            Path.home(), "Downloads", "downloads_data", self.info_dict['data_key'], chunk_info['name'])
        if os.path.isfile(chunk_file) is False:
            # try. there can be a connection error due
            # to no internet or no server connection

            try:
                downloaded_chunk = requests.post(self.url+"/download_chunk.php",
                                                 data={'security_key': security_key,
                                                       'return_file': 'true',
                                                       'data_key': self.info_dict['data_key'],
                                                       'file_name': chunk_info['name']},
                                                 headers={'User-Agent': user_agent})

                if downloaded_chunk.status_code == 200:

                    if len(downloaded_chunk.content) != 0:

                        """Checking file integrity. chunk_name is the sha-256 hash
                        of the file. if the hash doesnt match. then cancel the download
                        and warn the user"""

                        iv = downloaded_chunk.content[0:16]
                        key = bytes.fromhex(chunk_info['key'])
                        decrypted_chunk = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(
                            downloaded_chunk.content[16:]), AES.block_size)

                        with open('k.png', 'wb') as sb:
                            sb.write(decrypted_chunk)
                        chunk_hash = hashlib.sha256(
                            decrypted_chunk).hexdigest()

                        # print(chunk_info['hash'])
                        if chunk_hash == chunk_info['hash']:
                            logging.info("hash matched: "+chunk_info['name'])
                            with open(chunk_file, 'wb') as chunk_file:

                                chunk_file.write(decrypted_chunk)
                                # increasing the progress bar
                                self.progress_bar(
                                    80, int(self.info_dict['chunk_count']))
                        else:
                            file_compromised_queue.put(chunk_info['name'])
                            logging.info(
                                "File has been tempared: "+chunk_info['name'])
                            console_display(
                                ["Dont Open the file. File has been compromised.", "ERROR"]
                            )

                    else:
                        console_display(["Chunk not found in server", "ERROR"])
                        # self.check_for_chunks()
                else:
                    logging.error("chunk: "+chunk_info['name'] +
                                  " status code: "+downloaded_chunk.status_code)

            except ConnectionError as e:
                print(e)
                logging.warning(
                    "No internet connection in download chunk thread"
                )
                console_display(
                    ["No internet connection, Trying in 5 seconds", "ERROR"]
                )
                # if self.download_chunk_thread_count >= 30:
                #     self.download_chunk_thread_count = 0
                #     download_button.configure(state=tk.NORMAL)
                #     return
                """proper timeout function required"""

                # again try after 2 second. this should be configurabe
                # a new worker will continue the downlaod when internet
                # is available again
                download_chunk_queue.put(chunk_info)

            except Exception as e:
                # if there is something else other than
                # connectionerror then print it
                print(e)

        else:
            """
            there is already a file with chunk['name']. if hash
            matches, then keep the file and increase progress bar.
            otherwise delete the file and put the chunk_name
            into download_chunk_queue to redownload
            """
            chunk_hash = hashlib.sha256(
                open(chunk_file, "rb").read()).hexdigest()

            if chunk_hash == chunk_info['hash']:
                #print("hash matched")
                #logging.info("hash matched: "+chunk_info['name'])
                self.progress_bar(80, int(self.info_dict['chunk_count']))
                self.download_exists_queue.put(chunk_info['name'])
            else:

                os.remove(chunk_file)
                download_chunk_queue.put(chunk_info)

        # poping a entry from the queue
        # so a new worker will be created
        # in download_chunks_main()
        active_workers.get()

    def mergefiles(self):
        print('merge files')
        start = timeit.default_timer()
        console_display("Finishing up downloading")
        finished_file_name = os.path.join(
            Path.home(), "Downloads", self.info_dict['file_name'])

        # below there is two if. if the code is here
        # thit means one of it has to be true
        # file checking with below method is
        # not ideal. we should use some kind
        # of hashing to be 100% sure
        # print(os.path.join(Path.home(),
        #                  "Downloads", "downloads_data",
        #                 self.info_dict['data_key']))
        if os.path.isdir(os.path.join(Path.home(),
                                      "Downloads", "downloads_data", self.info_dict['data_key'])):

            temp_chunk_count = len(os.listdir(os.path.join(
                Path.home(), "Downloads", "downloads_data", self.info_dict['data_key'])))
            logging.info("temp chunk count: "+str(temp_chunk_count))

        else:
            # set to zero otherwise it will throw
            # error bellow
            temp_chunk_count = 0

        """if os.path.isfile(finished_file_name):
            # file chunks folder is not present.
            # so we will check if the file size
            # is same as info_dict['file_size']

            if os.path.isfile(finished_file_name):
                if os.path.getsize(finished_file_name) == int(self.info_dict['file_size']):
                    if_file_exist_evaluate_filesize = True"""

        # both chunk count should be int or str
        if int(temp_chunk_count) == int(self.info_dict['chunk_count']):
            # we have all the required chunks.
            # merging all the chunks

            with open(finished_file_name, 'wb') as f:
                for chunk_info in self.info_dict['file_serial']:
                    # print(chunk_info)
                    with open(os.path.join(Path.home(), "Downloads", "downloads_data",
                                           self.info_dict['data_key'],
                                           chunk_info['name']), "rb") as temp:
                        chunk = temp.read()
                    f.write(chunk)
                    # print("ch: ", 18, int(self.info_dict['chunk_count']))
                    # print("progress 3")
                    # increasing progress bar
                    # 18% is allocated for merging
                    self.progress_bar(
                        18, int(self.info_dict['chunk_count']))

            download_button.configure(state=tk.NORMAL)
            stop = timeit.default_timer()
            console_display('Merging Files took ' +
                            str(int(stop - start)) + " seconds.")

            logging.info("progress bar should be full now")
            # print("progress 790")
            if self.download_exists_queue.qsize() > 0:
                temp_chunks_percentage = str(
                    (math.ceil(self.download_exists_queue.qsize()
                               / int(self.info_dict['chunk_count']))*100))
                console_display(
                    [temp_chunks_percentage+"% of the file was downloaded before.", "BLUE"])
                if upload_exists_queue.mutex:
                    upload_exists_queue.queue.clear()
                else:
                    try:
                        upload_exists_queue.queue.clear()
                    except Exception as e:
                        print(e)

            console_display("Chunks Download Completed: "
                            + self.info_dict['file_name'])
            print("open folder ")
            console_display(["Download Finished!", "SUCCESS"])
            self.open_folder_with_file()

            self.progress_bar(2, 1)

        else:
            # os.listdir below can throw error if the
            # folder to store chunks is not present
            # but for now it should work.
            # will be fixed in future update
            print(self.info_dict['chunk_count'])
            print(temp_chunk_count)

            list_dir_of_chunks_folder = os.listdir(os.path.join(Path.home(), "Downloads",
                                                                "downloads_data", self.info_dict['data_key']))

            for chunk_info in self.info_dict['file_serial']:
                if not (chunk_info['name'] in list_dir_of_chunks_folder):
                    print(chunk_info)
                    download_chunk_queue.put(chunk_info)

            if self.merge_files_try_count >= 5:
                console_display(
                    ["Files failed to download because files are not present on the server", "ERROR"])
                console_display(["Upload the file again", "ERROR"])
                self.merge_files_try_count = 0
                download_button.configure(state=tk.NORMAL)
                return
            self.merge_files_try_count += 1
            console_display(str(len(os.listdir(os.path.join(Path.home(), "Downloads",
                                                            "downloads_data", self.info_dict['data_key'])))) +
                            " of " + str(self.info_dict['chunk_count']) + " downloaded")

            console_display(
                ["There are some missing parts. Retrying", "ERROR"])
            console_display("Trying to find missing chunks in the server")

            # self.missing_chunks_is_retry = True
            # if len(os.listdir(os.path.join(Path.home(), "Downloads",
            #                                "downloads_data", self.info_dict['data_key']))) < int(self.info_dict['chunk_count']):
            #     # self.download_info_dict() #this reset the downlaod loop from begining
            #     time.sleep(wait_time_before_trying_missing_chunks_download)
            #     # self.missing_chunks_download()
            self.download_chunks_main()

    def open_folder_with_file(self):

        if os.path.isfile(os.path.join(Path.home(), "Downloads",
                                       self.info_dict['file_name'])) is True:

            # a hack fix to fetch latest directory data
            # do not use a while loop or any other loop
            # in tkinter mainloop.

            os.path.getmtime(os.path.join(Path.home(), "Downloads"))
            if os_platform == 'Windows':
                popen_open = 'explorer /select,"'+os.path.join(Path.home(
                ), "Downloads", self.info_dict['file_name'])+'"'
                subprocess.Popen(popen_open)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call(
                    [opener, os.path.join(Path.home(), "Downloads")])
            # print([popen_open])
        else:
            self.root.after(200, self.open_folder_with_file)


class UploadHandler():
    def __init__(self, data_file=None, url=hard_coded_url, data_key_box_str=None,
                 root=None, progress_bar=None):
        self.data_key_box_str = data_key_box_str
        self.data_key_box_str.set("muahhaha")
        self.progress_bar = progress_bar
        self.root = root
        self.url = url
        self.offset = 0
        self.active_workers = queue.Queue()
        self.raw_chunk_data_queue = queue.Queue()
        self.info_dict = {}
        self.progress_bar(False, 1)
        self.already_uploaded_list = None
        # reming "/" from url if exists
        if len(self.url) > 5:
            if self.url[-1] == "/":

                self.url = self.url[-1]
            # self.url = host_entry.get()
        else:
            console_display(["Please provide a valid server.", "ERROR"])
            upload_button_upload_section.configure(state=tk.NORMAL)
            select_file_button.configure(state=tk.NORMAL)
            return

        if os.path.isdir(os.path.join(Path.home(), "Downloads", "uploads_of_file_sharing")) is False:
            os.mkdir(os.path.join(Path.home(), "Downloads",
                                  "uploads_of_file_sharing"))

        # this counter are used to determine how many time certain
        # function has failed due to no inter or connection error to the server
        self.count_no_internet = 0
        self.threading_upload_count = 0
        self.download_chunk_thread_count = 0
        self.merge_files_try_count = 0
        self.missing_chunks_is_retry = False
        self.upload_dict_info_count = 0

        self.data_file = data_file
        self.data_key = os.path.basename(data_file).split(
            ".")[0].replace(" ", "_")+hashgen(data_file)
        if os.path.isdir(os.path.join(Path.home(), "Downloads", "uploads_of_file_sharing", self.data_key)) is False:
            os.mkdir(os.path.join(Path.home(), "Downloads",
                                  "uploads_of_file_sharing", self.data_key))

        if(os.path.getsize(data_file) <= 5*mb):
            self.info_dict['chunk_size'] = os.path.getsize(data_file)
            self.info_dict['chunk_count'] = 1

        else:
            self.info_dict['chunk_size'] = 5*mb
            self.info_dict['chunk_count'] = math.ceil(
                os.path.getsize(data_file) / self.info_dict['chunk_size'])

        self.file = open(data_file, "rb")
        # self.file_unique_identifier = hashlib.sha256(
        #     self.file.read(1000)).hexdigest()
        # print("file_unique identifier: ", self.file_unique_identifier)
        # self.file.seek(0)

        self.info_dict['data_key'] = hashlib.sha256(
            os.urandom(256)).hexdigest()

        self.data_key_box_str.set(self.info_dict['data_key'])
        self.info_dict_private_key = hashlib.sha512(
            os.urandom(256)).hexdigest()

        self.info_dict['file_name'] = os.path.basename(data_file)
        self.data_key = self.info_dict['data_key']
        self.info_dict['file_serial'] = []
        self.info_dict['file_size'] = os.path.getsize(data_file)

        logging.info("Minimum chunk size is " +
                     str(self.info_dict["chunk_size"]/mb)+" mb")
        logging.info("File is divided into " +
                     str(self.info_dict['chunk_count'])+" chunks.")

        console_display("File uploading started.")

        # security_key will be replaced with api_key
        self.security_key = security_key
        print("file size is ", os.path.getsize(data_file))
        print("chunk count is ", self.info_dict['chunk_count'])
        self.info_dict_setup_done = False
        self.progress_bar(1, 1)

    def upload_info_dict(self):
        """
        * uploads info_dict to server
        * should only be called after all chunks are uploaded
        """

        try:
            if self.info_dict['file_size'] < mb:
                _file_size = "{:.1f}".format(
                    self.info_dict['file_size'] / kb) + " KB"
            else:
                _file_size = "{:.1f}".format(
                    self.info_dict['file_size'] / mb) + " MB"

            if len(self.info_dict['file_name']) > 25:
                _file_name = self.info_dict['file_name'][0:25] + "..."
            else:
                _file_name = self.info_dict['file_name'][0:35]

            key = hashlib.sha256(os.urandom(512)).digest()

            # encrypting file_basic_info
            self.file_basic_info = {'file_name': _file_name,
                                    'file_size': _file_size,
                                    'message': '',
                                    'type': os.path.splitext(self.info_dict['file_name'])[1]
                                    }
            iv = os.urandom(16)
            file_chunk = AES.new(key, AES.MODE_CBC, iv).encrypt(
                pad(json.dumps(self.file_basic_info).encode(), AES.block_size))
            self.file_basic_info = iv + file_chunk

            # encrypting info_dict
            iv = os.urandom(16)
            file_chunk = AES.new(key, AES.MODE_CBC, iv).encrypt(
                pad(json.dumps(self.info_dict).encode(), AES.block_size))
            checksum = hashlib.sha256(json.dumps(
                self.info_dict).encode()).digest()
            self.info_dict = iv + file_chunk

            a = requests.post(url=self.url+"/process_info_dict.php",
                              data={'security_key': self.security_key,
                                    'upload_info_dict': 'true',
                                    'data_key': self.data_key,
                                    'info_dict_private_key': self.info_dict_private_key

                                    },
                              files={
                                  'info_dict': self.info_dict,
                                  'file_basic_info': self.file_basic_info
                              },
                              headers={'User-Agent': user_agent})
            print(a.content)
            self.progress_bar(2, 1)
            select_file_button.configure(state=tk.NORMAL)
            upload_button_upload_section.configure(state=tk.NORMAL)
            console_display(["File uploaded successfully", "SUCCESS"])
            self.data_key_box_str.set(
                "http://localhost:3000/"+"download/?&id="+self.data_key+"&key="+key.hex()+"&checksum="+checksum.hex())

        except ConnectionError as e:
            logging.error(e)
            if self.upload_dict_info_count >= 30:
                self.upload_dict_info_count = 0
                upload_button_upload_section.configure(state=tk.NORMAL)
                select_file_button.configure(state=tk.NORMAL)

                console_display(
                    ["Upload failed due to no internet, try again later.", "ERROR"])
                return
            console_display(
                ["No internet connection, Trying in 5 seconds", "ERROR"])
            self.upload_dict_info_count += 1
            time.sleep(5)
            main_processing_queue.put(self.upload_info_dict)

        except Exception as e:
            logging.error(e)

    def start_upload(self):
        """
        * inititates file upload
        * this function will be called periodically
        * and it will launch necessary threads to upload chunks
        * after assigning UploadHandler class. calling this
        * function once is enough
        """
        if not self.info_dict_setup_done:
            print("private key is ", self.info_dict_private_key)
            logging.info("private key is "+self.info_dict_private_key)
            if (requests.post(self.url+"/process_info_dict.php", data={
                'security_key': self.security_key,
                'set_info_dict': 'true',
                'data_key': self.data_key,
                'info_dict_private_key': self.info_dict_private_key
            }).json()['code'] == True):
                self.info_dict_setup_done = True
                logging.info("info_dict setup done")
                self.progress_bar(1, 1)
        if self.already_uploaded_list == None:

            self.already_uploaded_list = requests.post(self.url+"/already_uploaded_list.php", data={
                'security_key': self.security_key,
                'data_key': self.data_key},
                headers={'User-Agent': user_agent}
            ).json()['data']

            print(" already uploaded : ", self.already_uploaded_list)

        if self.file.tell() < self.info_dict['file_size']:
            if self.active_workers.qsize() < 5:
                """
                * if there is less then 5 working upload thread. then
                * it wil lread a specified file chunk. then encrypt 
                * it and put that chunk in a queue to upload
                """
                # file_chunk = self.file.read(self.info_dict['chunk_size'])

                # in bytes. should be saved in hex string
                key = hashlib.sha256(os.urandom(512)).digest()
                iv = os.urandom(16)
                _file_chunk = self.file.read(self.info_dict['chunk_size'])
                file_chunk = AES.new(key, AES.MODE_CBC, iv).encrypt(
                    pad(_file_chunk, AES.block_size))

                file_chunk = iv + file_chunk  # adding iv with chunk
                chunk_hash = hashlib.sha256(_file_chunk).hexdigest()
                chunk_name = hashlib.sha256(os.urandom(512)).hexdigest()
                self.info_dict['file_serial'].append({'name': chunk_name,
                                                      'hash': chunk_hash,
                                                      'key': key.hex()})

                self.raw_chunk_data_queue.put({
                    'file_chunk': file_chunk,
                    'chunk_name': chunk_name
                })
                self.active_workers.put(1)
                main_processing_queue.put(self.upload_in_chunks)

        elif self.active_workers.qsize() == 0:
            print("upload successfull")
            main_processing_queue.put(self.upload_info_dict)
            return

        main_processing_queue.put(self.start_upload)

    def upload_in_chunks(self):
        """it will upload one chunk of file"""
        if self.raw_chunk_data_queue.empty() is True:
            logging.info("No chunks to upload")
            return
        file_chunk_dict = self.raw_chunk_data_queue.get()

        try:
            if len(host_entry.get()) < 5:
                return

            if file_chunk_dict['chunk_name'] not in self.already_uploaded_list:
                # print("false")
                files = {'split_file': (file_chunk_dict['chunk_name'], file_chunk_dict['file_chunk'],
                                        'multipart/form-data')}

                data_obj = {'security_key': security_key,
                            'id': 1,
                            'file_name': file_chunk_dict['chunk_name'],
                            'data_key': self.info_dict['data_key']}

                # upload.php receiving data and files. need to configure
                # update
                #  print(self.url+"/upload.php")
                upload_req = requests.post(self.url+"/upload.php", files=files, data=data_obj,
                                           headers={'User-Agent': user_agent}).json()
                # print(upload_req)
                if upload_req['code'] == True or upload_req['file_exists'] == True:
                    self.progress_bar(96, int(self.info_dict['chunk_count']))

                else:
                    logging.warning('File not uploded: ' +
                                    file_chunk_dict['chunk_name'])
                    self.raw_chunk_data_queue.put(file_chunk_dict)

            else:
                upload_exists_queue.put(file_chunk_dict['chunk_name'])
                print('file exists: ', file_chunk_dict['chunk_name'])
                self.progress_bar(96, int(self.info_dict['chunk_count']))

        except ConnectionError as e:
            print(e)
            if self.threading_upload_count >= 30:
                self.threading_upload_count = 0
                upload_button_upload_section.configure(state=tk.NORMAL)
                select_file_button.configure(state=tk.NORMAL)

                console_display(
                    ["Upload failed due to no internet, try again later.", "ERROR"])
                return
            console_display(
                ["No internet connection, Trying in 5 seconds", "ERROR"])
            self.threading_upload_count += 1
            # seeing the file . so it can be read later
            print('priv file.tell(): ', self.file.tell())
            self.file.seek(self.file.tell() - self.info_dict['chunk_size'])
            print('after seek file.tell(): ', self.file.tell())
            main_processing_queue.put(self.upload_in_chunks)

        self.active_workers.get()


class App:
    # thanks to https://github.com/beenje/tkinter-logging-text-widget/blob/master/main.py
    # for the code. helped me a lot
    def __init__(self, root):
        self.root = root
        root.title('Simfy File Share')
        # root.iconbitmap(r"icon-0.xbm")
        img = tk.PhotoImage(file='support_files/icon.png')
        root.tk.call('wm', 'iconphoto', self.root._w, img)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # creating the panes
        vertical_pane = ttk.PanedWindow(self.root, orient=VERTICAL)
        vertical_pane.grid(row=0, column=0, sticky="nsew")

        horizontal_pane = ttk.PanedWindow(vertical_pane, orient=HORIZONTAL)
        vertical_pane.add(horizontal_pane)

        horizontal_down = ttk.PanedWindow(
            vertical_pane, orient=HORIZONTAL)  # down horizontal pan
        vertical_pane.add(horizontal_down)

        # creating the frames
        form_frame = ttk.Labelframe(
            horizontal_pane, text="Upload Area", borderwidth=10)
        form_frame.columnconfigure(1, weight=1)
        horizontal_pane.add(form_frame, weight=1)
        third_frame = ttk.Labelframe(
            horizontal_pane, text="Download Area", borderwidth=10)
        horizontal_pane.add(third_frame, weight=1)
        console_frame = ttk.Labelframe(
            horizontal_down, text="File Status", borderwidth=5)
        horizontal_down.add(console_frame, weight=1)

        # assigning the frames
        self.console = ConsoleUi(console_frame, self.root)
        self.form = UploadSection(form_frame, self.root, self.console)
        self.third = DownloadSection(third_frame, self.root, self.console)
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        signal.signal(signal.SIGINT, self.quit)
        self.root.after(100, self.execute_idle_process)

    def execute_idle_process(self):
        # tkinter root will check this function
        # every 100 miliseconds to see if there is
        # any work to do
        if not main_processing_queue.empty():
            proc = main_processing_queue.get()
            x = threading.Thread(target=proc)
            x.daemon = True
            x.start()
        self.root.after(100, self.execute_idle_process)

    def quit(self, *args):
        self.root.destroy()


def main():
    logging.basicConfig(level=logging.ERROR)
    root = tk.Tk()
    app = App(root)
    app.root.mainloop()


if __name__ == "__main__":
    main()
