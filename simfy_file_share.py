# Author: Ashraful Firoz
# There are some repetative code here and there. 
# I will try to fix them in the next update
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
import pyperclip #sudo apt-get install xclip for linux
from pathlib import Path
from tkinter.scrolledtext import ScrolledText
import psutil
import platform
from tkinter import ttk, VERTICAL, HORIZONTAL, N, S, E, W, NW, SE, SW
from config import hard_coded_url, most_working_thread
from config import wait_time_before_trying_missing_chunks_download 
from config import wait_time_before_trying_failed_uploads, security_key 

# important notice: files are not encrypted 
# so its as safe as the hosting used
# security_key is the key thats going to be used
# to validate if you have access to the server
# on the server side. every request will check 
# if the security key match.
# in the auth.php on the server section you can
# define security_key. make sure they both math
# otherwise server response will be invalid 

# every file has a unique security key. thats refered as 
# data_key or info_dict['dir_to_save_chunk']

# this user agent will be sent to the server with post.
# without a proper user agent some shared hosting 
# will block the request
user_agent = """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"""


os_platform = platform.system() # os_platform="Linux" for linux platforms
download_chunk_queue = queue.Queue()
failed_chunk_queue = queue.Queue()
upload_exists_queue = queue.Queue()
download_exists_queue = queue.Queue()
main_processing_queue = queue.Queue()

logger = logging.getLogger(__name__)



#this is to calculate chunk size
kb = 1000
mb = kb * 1000


def hashgen(data_file):
    """this function is used to create unique
    data key/security key"""
    with open(data_file, 'rb') as f:
        hash_data = f.read(2000)
    return hashlib.md5(hash_data).hexdigest()



class UploadSection:
    """This is the Upload Data section"""
    def __init__(self, frame, root, console):
        #self console prints the console data
        #declaring classwide variables
        self.console = console
        self.frame = frame
        self.filename = ""
        self.data_key = ""
        self.root = root
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


        photo_choose_file_button = tk.PhotoImage(master = self.root, file='support_files/sf.png')
        select_file_button = tk.Button(frame, text="choose file",image = photo_choose_file_button,
                                       command=self.select_file,height = 60, borderwidth=1,
                                       width = 180) #relief = "solid"
        select_file_button.grid(column = 0, padx = 10,row=0, sticky = E)
        
        
        photo_upload_button = tk.PhotoImage(master = self.root, file='support_files/up.png')
        upload_button_upload_section = tk.Button(frame,text = "Upload", image = photo_upload_button,
                                                    command = self.upload_selected_file,height = 60,
                                                    width = 200, borderwidth=1)
        upload_button_upload_section.grid(column=1,row=0, pady = 10, sticky = W)
        
        tk.Label(self.frame, text='Server:').grid(column=0, row=1,sticky = W)
        self.host_entry = tk.Entry(frame, textvariable=tk.StringVar(frame, value=hard_coded_url),width=25)
        self.host_entry.grid(column=1, row=1, sticky=(W, E), pady = 10)
        global host_entry 
        host_entry = self.host_entry
        
        
        global host_down_power_button_photo
        host_up_power_button_photo = tk.PhotoImage(master = root, file='support_files/host_on.png')
        host_down_power_button_photo = tk.PhotoImage(master = root, file='support_files/host_off.png')
        self.host_power_button = tk.Button(frame, text = "Turn Host On/OFF", image = host_down_power_button_photo,
                                            command = self.update_host_entry_box, 
                                            height = 20, width = 20)
        self.host_power_button.grid(row=1, column= 2)
        # host_entry should be disabled for basic. 
        # set the basic host in support_files/config.txt
        self.host_entry.configure(state=tk.DISABLED)
        tk.Label(self.frame, text='File Security Key:').grid(column=0, row=2, sticky = W,pady = 5)
        
        self.data_key_box_str = tk.StringVar(frame, value='')
        self.data_key_box= tk.Entry(frame, width=25,textvariable=self.data_key_box_str)
        self.data_key_box.grid(column=1, row=2, sticky=(W, E))
        
        photo_data_key_button  = tk.PhotoImage(master = self.root, file='support_files/cp.png')
        tk.Button(frame,text = "copy file security key \nto clipboard",
                                        image = photo_data_key_button ,
                                        command = self.copy_data_key , height = 24,
                                        width = 24, borderwidth=1).grid(column=2,row=2, padx = 10)
        
        #this is the styling for using %number on thep rogressbar
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
        # create progressbar
        self.variable = tk.DoubleVar(root)
        self.pbar = ttk.Progressbar(self.frame,length = 410, style='text.Horizontal.TProgressbar', variable=self.variable)
        self.pbar.grid(row = 3, column =0, columnspan=3, pady = 10, padx = 4, sticky = W)

        self.download_speed_var = tk.StringVar()
        self.download_speed_var.set('Upload speed: 0.00 Mbps')
        self.download_label = tk.Label(self.frame,textvariable = self.download_speed_var,
                                          width = 30)
        self.download_label.grid(column = 0, row=4, columnspan=3,sticky = N)
        self.download_label.configure(borderwidth = 0)
    
        self.pid = os.getpid()
        print("pid: ", self.pid)
        #this is to get the network card to monitor network speed
        # this speed checker currenty displays the whole system's 
        # network speed
        visit_ex = threading.Thread(target = self.visit_example)
        visit_ex.daemon = True
        visit_ex.start()
    
    def visit_example(self):
        self.list1 = []
        self.network_card = False
        self.card_list = []
        for card in psutil.net_io_counters(pernic=True):
            self.list1.append(psutil.net_io_counters(self.pid)[card].bytes_sent)
            self.card_list.append(card)
        
        for card in psutil.net_io_counters(pernic=True):
            self.list1.append(psutil.net_io_counters(self.pid)[card].bytes_sent )
        

        try:
            requests.post("https://example.com")
            requests.post("https://example.com")
            requests.post("https://example.com")
        except Exception as e:
            print(e)
        
        list2 = []
        for card in psutil.net_io_counters(pernic=True):
            list2.append(psutil.net_io_counters(self.pid)[card].bytes_sent )

        for i in range(len(list2)):
            if (list2[i] - self.list1[i]) > 10:
                self.network_card = self.card_list[i]

        print(self.network_card)
        self.root.after(100, self.check_speed)
       

    def check_speed(self):
        x = threading.Thread(target = self.upload_download_speed_checker)
        x.daemon = True
        x.start()

    def upload_download_speed_checker(self):
        """This function checks upload speed"""
        try:
            last_time = time.time()
            last_bytes = psutil.net_io_counters(pernic=True)[self.network_card].bytes_sent
            while True:
                now_bytes = psutil.net_io_counters(pernic=True)[self.network_card].bytes_sent
                now_time = time.time()
                down_speed = (((now_bytes - last_bytes) / (now_time - last_time)) / 1000000.00)*8.00
                self.download_speed_var.set("Upload speed: {:.3f} Mbps".format(down_speed))
                last_time = now_time
                last_bytes = now_bytes
                time.sleep(1)
        except:
            self.root.after(200, self.upload_download_speed_checker)

    def update_host_entry_box(self):
        #self.host_entry.configure(state=tk.NORMAL)
        if self.host_entry['state'] == tk.NORMAL:
            self.host_entry.configure(state=tk.DISABLED)
            self.host_power_button.configure(image = host_down_power_button_photo)
        else:
            self.host_entry.configure(state=tk.NORMAL)
            self.host_power_button.configure(image = host_up_power_button_photo)
    
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
        self.filename = filedialog.askopenfilename(initialdir = "",title = "Select file",
                                               filetypes = (("all files","*.*"),
                                                            ("exe files", "*.exe"),
                                                            ("jpeg files","*.jpg")))
        if len(self.filename) > 0:
            self.console.display( "File selected: "+ self.filename.split("/")[-1])

        else:
            self.console.display(["No File Selected", "WARNING"])
        
        
    
    def upload_selected_file(self):
        if len(self.filename) != 0:
            print(self.filename)
            #logg.set("file "+root.filename + " selected")

            final_host = self.host_entry.get()
            if len(final_host) < 5:
                self.console.display(["Please provide a valid server url", "ERROR"])
                return
            self.console.display( "Using server: "+final_host)
            self.upload_progress_bar(False, 1)
            file_upload = FileHandle(data_file = self.filename, url = final_host, console = self.console,
                                    root = self.root, progress_bar = self.upload_progress_bar,
                                    data_key_box_str = self.data_key_box_str, filename=self.filename)
            
            #putting file_upload.splitfiles() in the main queue to execute
            main_processing_queue.put(file_upload.splitfiles)
            select_file_button.configure(state=tk.DISABLED)
            upload_button_upload_section.configure(state=tk.DISABLED)
            
        else:
            self.console.display("Please choose a file before pressing upload")
            


class DownloadSection:
    """Class of download data section. pass 
    downlaod data frame, root, console"""
    def __init__(self, frame, root, console):
        self. root = root
        self.console = console
        self.frame = frame
        
        tk.Label(self.frame, text='File Security Key:').grid(column=0, row=1, sticky=W, pady = 10)
        self.data_key_box_var = tk.StringVar(frame,value="")
        self.data_key_box = tk.Entry(frame, width=40, textvariable = self.data_key_box_var)
        self.data_key_box.grid(column=1, row = 1, sticky = (W, E), padx = 10)
        
        global photo_paste_button
        photo_paste_button = tk.PhotoImage(master = self.frame, file='support_files/pt.png')
        tk.Button(self.frame, text="Paste", image = photo_paste_button,
                    command = self.paste_to_data_key, height = 18,
                    width = 18).grid(column = 2, row = 1, padx = 2, sticky = W)

        global photo_download_button 
        photo_download_button  = tk.PhotoImage(master = self.root, file='support_files/dn.png')
        global download_button
        download_button = tk.Button(frame,text = "Download",image = photo_download_button , 
                  command = self.download_files_from_host,height = 60,
                  width = 200)
        download_button.grid(column=0,row=2,padx = 15,pady=4, columnspan=2, sticky = W )
        
        global change_download_folder_photo
        change_download_folder_photo = tk.PhotoImage(master = self.root, file='support_files/download_folder.png')
        tk.Button(frame,text = "Downloads Folder",image = change_download_folder_photo , 
                  command = self.change_download_folder ,height = 60,
                  width = 78).grid(column=1,row=2,sticky = E, padx =5 )

        tk.Label(self.frame, text='Server:').grid(column=0, row=0, sticky = W)
        self.down_host_box_var = tk.StringVar(frame,value=hard_coded_url)
        self.host_entry = tk.Entry(frame, textvariable = self.down_host_box_var, width=40)
        self.host_entry.grid(column=1, row=0, sticky = (W, E), pady = 10, padx = 10)


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
        self.dbar = ttk.Progressbar(self.frame,length = 370, style='text.Horizontal.TProgressbar_d', variable=self.vari)
        self.dbar.grid(row = 3, column =0, columnspan=3,  pady = 10,padx = 4, sticky = SW)
        
        self.host_power_button = tk.Button(frame, text = "Turn Host On/OFF", image = host_down_power_button_photo,
                                            command = self.update_host_entry_box, 
                                            height = 20, width = 20)
        self.host_power_button.grid(row=0, column= 2, sticky = W)
        self.host_entry.configure(state=tk.DISABLED)

        self.download_speed_var = tk.StringVar()
        self.download_speed_var.set('Download speed: 0.00 Mbps')
        self.download_label = tk.Label(self.frame,textvariable = self.download_speed_var,
                                          width = 30)
        self.download_label.grid(column = 0, row=4, columnspan=3,sticky = N)
        self.download_label.configure(borderwidth = 0)
        #tk.Label(self.frame,text="pani" ,height =5, width =10).grid(row = 4, column =1)
    
        visit_ex = threading.Thread(target = self.visit_example)
        visit_ex.daemon = True
        visit_ex.start()
    
    def visit_example(self):
        self.list1 = []
        self.network_card = False
        self.card_list = []
        for card in psutil.net_io_counters(pernic=True):
            self.list1.append(psutil.net_io_counters(pernic=True)[card].bytes_sent)
            self.card_list.append(card)
        
        for card in psutil.net_io_counters(pernic=True):
            self.list1.append(psutil.net_io_counters(pernic=True)[card].bytes_sent )
        
        try:
            #generating some trafic so that psutil returns value greater than 10
            requests.post("https://example.com")
            requests.post("https://example.com")
            requests.post("https://example.com")
        except Exception as e:
            print(e)
        
        list2 = []
        for card in psutil.net_io_counters(pernic=True):
            list2.append(psutil.net_io_counters(pernic=True)[card].bytes_sent )

        for i in range(len(list2)):
            if (list2[i] - self.list1[i]) > 10:
                self.network_card = self.card_list[i]

        print(self.network_card)
        self.root.after(100, self.check_speed)


    def check_speed(self):
        x = threading.Thread(target = self.upload_download_speed_checker)
        x.daemon = True
        x.start()


    def upload_download_speed_checker(self):
        last_time = time.time()
        last_bytes = psutil.net_io_counters(pernic=True)[self.network_card].bytes_recv
        while True:
            now_bytes = psutil.net_io_counters(pernic=True)[self.network_card].bytes_recv
            now_time = time.time()
            down_speed = (((now_bytes - last_bytes) / (now_time - last_time)) / 1000000.00)*8.00
            self.download_speed_var.set("Download speed: {:.3f} Mbps".format(down_speed))
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
            opener ="open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, path])

    def update_host_entry_box(self):
        #self.host_entry.configure(state=tk.NORMAL)
        if self.host_entry['state'] == tk.NORMAL:
            self.host_entry.configure(state=tk.DISABLED)
            self.host_power_button.configure(image = host_down_power_button_photo)
        else:
            self.host_entry.configure(state=tk.NORMAL)
            self.host_power_button.configure(image = host_up_power_button_photo)
    
    def paste_to_data_key(self):
        self.data_key_box_var.set(pyperclip.paste())
        #self.root.update_idletasks()
        #self.root.update()

       


    def download_progress_bar(self, a, b):
        if a == False:
            self.dbar['value'] = 0  # increment progressbar 
            self.vari.set(0.00)
            self.style_d.configure('text.Horizontal.TProgressbar_d', 
                        text='{:.2f} %'.format(0.00))
            #self.root.update_idletasks()
            #self.root.update()

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
        if len(self.host_entry.get()) < 0:
            self.console.display("Please provide a valid server url.", "ERROR")
        download_button.configure(state=tk.DISABLED)

        self.download_progress_bar(False, 1)
        if(len(data_key) > 0):
           
            self.download_progress_bar(1, 1)
            temp_files = FileHandle(info_dict ={'dir_to_save_chunk' : data_key},
                                    url = self.host_entry.get(), console = self.console,  root = self.root, progress_bar=self.download_progress_bar)
            
            #putting download_info_dict in the main
            # processing queue and getting the chain started
            main_processing_queue.put(temp_files.download_info_dict)
          
        else:
            download_button.configure(state=tk.NORMAL)
            print("Please provide a File Security Key first then press Download")
            self.console.display("Please provide a File Security Key first then press Download")
        

             

class ConsoleUi:
    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, frame, root):
        self.root = root
        self.frame = frame
        self.global_queue = queue.Queue()
        self.qu_count = 0

        # Create a ScrolledText wdiget
        

        self.scrolled_text = ScrolledText(frame, state='disabled', height=5, width = 107)
        self.scrolled_text.grid(row=1, column=0, columnspan = 2, padx = 10, pady = 10, sticky=(N, S, W))

        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        self.scrolled_text.tag_config('SUCCESS', foreground='green')
        self.scrolled_text.tag_config('BLUE', foreground='blue')
        
        
        self.frame.after(100, self.poll_log_queue)
    
    def display(self, record):
        #msg = record
        self.global_queue.put(record)
        

    def poll_log_queue(self):
        #for _ in range(len(self.global_queue)):
        #if (self.qu_count < len(self.global_queue)):
        if not self.global_queue.empty():
            msg = self.global_queue.get()
            self.scrolled_text.configure(state='normal')
            if type(msg) == type(str()):
                self.scrolled_text.insert(tk.END, str(self.qu_count)+": "+msg +" "+ '\n', "INFO")

            else:
                self.scrolled_text.insert(tk.END, str(self.qu_count)+": "+msg[0] +" "+ '\n', msg[1])#, record.levelname)
            self.scrolled_text.configure(state='disabled')
            # Autoscroll to the bottom
            self.scrolled_text.yview(tk.END) #scrolling view to end, IG
            self.qu_count += 1
            if not self.global_queue.empty():
                self.root.after(10, self.poll_log_queue)
            
        
        self.frame.after(100, self.poll_log_queue)




    #logger.log(lvl, self.message.get())



class FileHandle():
    def __init__(self, data_file=None, info_dict = {}, url=hard_coded_url, console=None, root=None, progress_bar = None,
    data_key_box_str = None, filename = None):
        self.progress_bar = progress_bar
        self.data_key_box_str = data_key_box_str
        self.filename = filename
        self.root = root
        self.console = console
        if len(host_entry.get()) > 5:
            self.url = host_entry.get()
        else:
            self.console.display(["Please provide a valid server.", "ERROR"])
            upload_button_upload_section.configure(state=tk.NORMAL)
            select_file_button.configure(state = tk.NORMAL)
            return
        self.info_dict = info_dict
        self.secure_key = "123456"
        if os.path.isdir(os.path.join(Path.home(), "Downloads","uploads_of_file_sharing")) is False:
            os.mkdir(os.path.join(Path.home(), "Downloads", "uploads_of_file_sharing"))
            
        if os.path.isdir(os.path.join(Path.home(), "Downloads")) is False:
            os.mkdir(os.path.join(Path.home(), "Downloads"))
        if os.path.isdir(os.path.join(Path.home(), "Downloads", "downloads_data")) is False:
            os.mkdir(os.path.join(Path.home(), "Downloads", "downloads_data"))
        if len(self.info_dict) > 1:
            self.dir_to_save_chunk = info_dict['dir_to_save_chunk']

        #this counter are used to determine how many timer certain 
        #function has failed due to no inter or connection error to the server
        self.count_no_internet = 0
        self.threading_upload_count = 0
        self.download_chunk_thread_count = 0
        self.merge_files_try_count = 0
        self.missing_chunks_is_retry = False
        #missing_chunks_is_retry = False
        if data_file is not None:
            self.data_file = data_file
            self.dir_to_save_chunk = os.path.basename(data_file).split(".")[0].replace(" ", "_")+hashgen(data_file) 
            if os.path.isdir(os.path.join(Path.home(), "Downloads", "uploads_of_file_sharing", self.dir_to_save_chunk)) is False:
                os.mkdir(os.path.join(Path.home(), "Downloads", "uploads_of_file_sharing", self.dir_to_save_chunk))


            if(os.path.getsize(data_file) <= 5*mb):
                self.chunk_size = os.path.getsize(data_file)
                self.chunk_count = 1
            else:
                self.chunk_size = 5*mb
                self.chunk_count = math.ceil(os.path.getsize(data_file) / self.chunk_size)
            
            self.info_dict["chunk_size"] = self.chunk_size
            self.info_dict["chunk_count"] = self.chunk_count
            self.info_dict['dir_to_save_chunk'] = self.dir_to_save_chunk
            self.info_dict['file_serial'] = {}
            self.info_dict['extension'] = os.path.basename(data_file).split(".")[-1]  #track records of id and file name
            self.info_dict['file_size'] = os.path.getsize(data_file)
            
            self.console.display( "Minimum chunk size is "+ str(info_dict["chunk_size"]/mb)+" mb")
            self.console.display( "File is divided into "+ str(info_dict['chunk_count'])+" chunks.")

        
    
    def splitfiles(self):
        start = timeit.default_timer()
        try:
            #if error with host
            print(self.data_file)
        except:
            upload_button_upload_section.configure(state=tk.NORMAL)
            select_file_button.configure(state = tk.NORMAL)
            return 
        with open(self.data_file, "rb") as f:
            for idd in range(self.info_dict['chunk_count']):
                chunk = f.read(self.info_dict['chunk_size'])
                chunk_file_name = hashlib.md5(chunk).hexdigest()
                
                tempname = os.path.join( Path.home(), "Downloads", "uploads_of_file_sharing", self.dir_to_save_chunk, chunk_file_name)
                if os.path.isfile(tempname) is False:
                    with open(tempname, "wb") as w:
                        w.write(chunk)
                       
                self.info_dict['file_serial'][str(idd)] = chunk_file_name 
                #print("progress 651")
                self.progress_bar(20, int(self.info_dict['chunk_count']))
                

        self.data_key_box_str.set(self.info_dict['dir_to_save_chunk'])
        main_processing_queue.put(self.upload_dict_info)
        stop = timeit.default_timer()
        self.upload_dict_info_count = 0
        self.console.display( 'Spilitting files took '+ str(int(stop - start))+" seconds." ) 
        
                
    def upload_dict_info(self):
        """should only be called after split files. other info_dict will be broken"""
        
        try:
            requests.post(url = self.url+"/dict_up.php",
                    data={'security_key': security_key, 'info_dict' : json.dumps(self.info_dict),
                        'data_key' : self.info_dict['dir_to_save_chunk']},
                         headers = {'User-Agent' : user_agent})

            #print(chunk_verify.text)
            print("dict upload done")
            main_processing_queue.put(self.upload_chunks)
            #break break if all goes well
        except ConnectionError as e:
            print(e)
            print("error in dict up")
            if self.upload_dict_info_count >= 30:
                self.upload_dict_info_count = 0
                upload_button_upload_section.configure(state=tk.NORMAL)
                select_file_button.configure(state = tk.NORMAL)
                
                self.console.display(["Upload failed due to no internet, try again later.", "ERROR"])
                return
            self.console.display(["No internet connection, Trying in 5 seconds", "ERROR"])
            self.upload_dict_info_count +=1
            self.root.after(5000, self.upload_dict_info)
            #self.root.update_idletasks()
            #self.root.update()
        except Exception as e:
            print(e)
            
        
        

    def download_info_dict(self):
        
        self.missing_chunks_is_retry = False
        try:
            print("info")
            self.console.display("File download started")
            revive_data_req = requests.post(self.url+"/dict_up.php",
                                            data={'security_key': security_key,
                                            'data_key': self.info_dict['dir_to_save_chunk'],
                                            "secure_key": self.secure_key,'download_info_dict': 'true'},
                                            headers = {'User-Agent' : user_agent})
            if(len(revive_data_req.text)) == 0:
                
                self.console.display(["File not found for security key: "+ self.info_dict['dir_to_save_chunk'], "ERROR"])
                #print("progress 710")
                self.progress_bar(False, 1)
                download_button.configure(state=tk.NORMAL)
                #self.root.update_idletasks()
                #self.root.update()
                return
            #return #to return from function
            self.info_dict = json.loads(revive_data_req.text)
            #global info_dict_pr
            #info_dict_pr = self.info_dict
            #print(self.info_dict)
            self.console.display("File Information Downloaded")
            
            print("info dict downloaded")
            if(len(self.info_dict) <=1):
                self.console.display("File not found on server")
                print("File not found on server")
                download_button.configure(state='tk.NORMAL')
                return
            #print("progress 730")
            self.progress_bar(1, 1)
            self.console.display("Downloading Chunks")
            global if_download_file_exists
            
            if_download_file_exists = False
            if os.path.isfile(os.path.join(Path.home(), "Downloads",
                            self.info_dict['dir_to_save_chunk'][0:-32])+ "."+self.info_dict['extension']):
                if_download_file_exists = True
                main_processing_queue.put(self.mergefiles)

            else:
                main_processing_queue.put(self.download_chunks)

        except ConnectionError as e:
            print(e)
            if (self.count_no_internet > 30):
                self.console.display(["Failed to download file due to no internet, try again later.", "ERROR"])
                self.count_no_internet = 0
                return

            self.console.display(["No internet. Cant download file information.", "ERROR"])
            self.count_no_internet += 1
            self.root.after(3000, self.download_info_dict)
        except Exception as e:
            print(e)
       
        #defaul url is lcoalhsot. so when I save that it also stores that to the info dict
        #dictionary. so we need to store our new url and replace it with localhost
        #self.info_dict['url'] = temp_url
        
        
        

            
    def mergefiles(self):
        start = timeit.default_timer()  
        temp_merge_completed = True     
        #self.console.display(str(already_exists)+" of "+str(self.info_dict['chunk_count'])+ " files already exists")
        self.console.display("Finishing up downloading")
        #input(" enter to forware")
        temp_chunk_count = str(len(os.listdir(os.path.join(Path.home(), "Downloads","downloads_data", self.info_dict['dir_to_save_chunk']))))
        #self.info_dict = info_dict_pr
        #print(self.info_dict)
        finished_file_name = (os.path.join(Path.home(), "Downloads",
                                   self.info_dict['dir_to_save_chunk'][0:-32])+"."+self.info_dict['extension'])
            

        if_file_exist_evaluate_filesize = False
        if os.path.isfile(finished_file_name):
            if os.path.getsize(finished_file_name) == int(self.info_dict['file_size']):
                if_file_exist_evaluate_filesize = True

        if temp_chunk_count == str(self.info_dict['chunk_count']) or if_file_exist_evaluate_filesize:
           
            if (not os.path.isfile(finished_file_name)) or (not if_file_exist_evaluate_filesize):
                with open(finished_file_name, 'wb') as f:
                    for key in self.info_dict['file_serial']:
                        with open(os.path.join(Path.home(), "Downloads","downloads_data",
                                            self.info_dict['dir_to_save_chunk'],
                                            self.info_dict['file_serial'][key]), "rb") as temp:
                            chunk = temp.read()
                        f.write(chunk)
                        #print("ch: ", 18, int(self.info_dict['chunk_count']))
                        #print("progress 3")
                        self.progress_bar(18, int(self.info_dict['chunk_count']))
            else:
                
                #print("progress 780")
                self.progress_bar(18, 1)
                self.console.display(["File Already Exists", "SUCCESS"])
            download_button.configure(state=tk.NORMAL)
            stop = timeit.default_timer()
            self.console.display( 'Merging Files took '+ str(int(stop - start)) + " seconds.")
            self.missing_chunks_is_retry = False
            print("missing_chunks_is_Retry at mergefiles: ", self.missing_chunks_is_retry)
                
                
            #print("progress 790")
            self.progress_bar(2,1)
            
        else:
            temp_merge_completed = False
            list_dir_of_chunks_folder = os.listdir(os.path.join(Path.home(), "Downloads",
                                        "downloads_data", self.info_dict['dir_to_save_chunk']))
            for idd in self.info_dict['file_serial']:
                if self.info_dict['file_serial'][str(idd)] not in list_dir_of_chunks_folder:
                    download_chunk_queue.put(idd)
            #print( download_chunk_queue.qsize())
            #print(idd)
            #print(list_dir_of_chunks_folder)
            print(self.info_dict['file_serial'])
            if self.merge_files_try_count >=5:
                self.console.display(["Files failed to download because files are not present on the server", "ERROR"])
                self.console.display(["Upload the file again", "ERROR"])
                self.merge_files_try_count = 0
                download_button.configure(state=tk.NORMAL)
                return
            self.merge_files_try_count += 1
            self.console.display(str(len(os.listdir(os.path.join(Path.home(), "Downloads",
                        "downloads_data",self.info_dict['dir_to_save_chunk'])))) +
                       " of " + str(self.info_dict['chunk_count']) + " downloaded")
            self.console.display(["There are some missing chunks. Retrying", "ERROR"])
            self.console.display("Trying to find missing chunks in the server")
            
            self.missing_chunks_is_retry = True
            if len(os.listdir(os.path.join(Path.home(), "Downloads",
                        "downloads_data",self.info_dict['dir_to_save_chunk']))) < int(self.info_dict['chunk_count']):
                #self.download_info_dict() #this reset the downlaod loop from begining
                time.sleep(wait_time_before_trying_missing_chunks_download)
                self.missing_chunks_download()

        if temp_merge_completed:
            # if merging done then this will wxwcute. other wise 
            # temp_merge_completed will be false on else section

            print("downoload completed")
            #download_button.configure(state=tk.NORMAL)
            if download_exists_queue.qsize() > 0:
                temp_chunks_percentage = str((download_exists_queue.qsize()/int(self.info_dict['chunk_count']))*100)
                self.console.display([temp_chunks_percentage+"% of the file was downloaded before.", "BLUE"])
                if upload_exists_queue.mutex:
                    upload_exists_queue.queue.clear()
                else:
                    try:
                        upload_exists_queue.queue.clear()
                    except Exception as e:
                        print(e)
            if if_download_file_exists:
                self.progress_bar(100,1)
            self.console.display("Chunks Download Completed: "
                                + self.info_dict['dir_to_save_chunk'][0:-32]
                                + "."+self.info_dict['extension'])
            print("open folder ")
            self.console.display(["Download Finished!", "SUCCESS"])
            self.open_folder_with_file()

        
        
    def threading_upload(self,idd, url):
        try:
            if len(host_entry.get()) < 5:
                return
            temp_req_file_count_exist_check = requests.post(host_entry.get()+"/file_count.php",
                    data = {'security_key': security_key,
                    "data_key" : self.info_dict['dir_to_save_chunk'],
                    "file_name" : self.info_dict['file_serial'][str(idd)]},
                     headers = {'User-Agent' : user_agent} ).text

            if  temp_req_file_count_exist_check == "False":
                #print("false")
                files = {'split_file' : (self.info_dict['file_serial'][str(idd)],
                                        open(os.path.join(Path.home(), "Downloads", "uploads_of_file_sharing", self.info_dict['dir_to_save_chunk'],
                                                        self.info_dict['file_serial'][str(idd)]), "rb"),
                                        'multipart/form-data')}

                data_obj = {'security_key': security_key,
                            'id' : idd,
                            'file_name': self.info_dict['file_serial'][str(idd)] ,
                            'data_key' : self.info_dict['dir_to_save_chunk']}
                
                a = requests.post(url, files=files, data=data_obj,
                            headers = {'User-Agent' : user_agent}) #finally uploading the file by post
                #self.console.display(a.text) 
                
                if a.text != self.info_dict['file_serial'][str(idd)] and a.text != 'file_exists':
                    failed_chunk_queue.put(idd)
                    
                print(a.text)
                self.console.display([a.text, "ERROR"])
              
            elif temp_req_file_count_exist_check == "True":
                #self.console.display("Chunk exist on server: " + self.info_dict['file_serial'][str(idd)])
                upload_exists_queue.put(self.info_dict['file_serial'][str(idd)])
            else:
                print("main_processing_queue.put: ", temp_req_file_count_exist_check)
                print("file not uploaded properly: 903")
                 #increase progress bar by the required value
        except ConnectionError as e:
            print(e)
            if self.threading_upload_count >= 30:
                self.threading_upload_count = 0
                upload_button_upload_section.configure(state=tk.NORMAL)
                select_file_button.configure(state = tk.NORMAL)
                
                self.console.display(["Upload failed due to no internet, try again later.", "ERROR"])
                return
            self.console.display(["No internet connection, Trying in 5 seconds", "ERROR"])
            self.threading_upload_count +=1
            self.root.after(5000, self.threading_upload, idd, url)
            #self.root.update_idletasks()
            #self.root.update()
        #print("progress 888")
        self.progress_bar(78, int(self.info_dict['chunk_count']))


    
    def upload_chunks(self):
        global upload_submit_thread
        upload_submit_thread = threading.Thread(target=self.upload_chunks_main)
        upload_submit_thread.daemon = True
        upload_submit_thread.start()
        self.root.after(500, self.check_upload_submit_thread)

    def check_failed_chunk_upload_thread(self):
        if self.missing_chunk_thread.is_alive():
            self.root.after(500, self.check_missing_chunk_thread)    
        else:
            self.check_upload_submit_thread()


    def failed_chunk_upload(self):

        temp_upload_idd_list = list()
        while failed_chunk_queue.empty() != True:
            temp_upload_idd_list.append(failed_chunk_queue.get())

        if failed_chunk_queue.mutex:
            failed_chunk_queue.queue.clear()
        else:
            try:
                failed_chunk_queue.queue.clear()
            except Exception as e:
                print(e)

        self.missing_chunk_thread = threading.Thread(target=self.upload_chunks_main() ,
                                            kwargs={'custom_idd': temp_upload_idd_list})
        
        self.missing_chunk_thread.daemon = True                                        
        self.missing_chunk_thread.start()
        self.root.after(500, self.check_failed_chunk_upload_thread)    


    def check_upload_submit_thread(self):
        if upload_submit_thread.is_alive():
            self.root.after(500, self.check_upload_submit_thread)
        else:
            if failed_chunk_queue.qsize() > 0:
                time.sleep(wait_time_before_trying_failed_uploads)
                self.failed_chunk_upload()
            else:
                #print("progress 935")
                self.progress_bar(2, 1)
                select_file_button.configure(state=tk.NORMAL)
                upload_button_upload_section.configure(state=tk.NORMAL)
                if upload_exists_queue.qsize() > 0:
                    temp_chunks_percentage = str((upload_exists_queue.qsize()/int(self.info_dict['chunk_count']))*100)
                    self.console.display([temp_chunks_percentage+"% of the file already existed in the server.", "BLUE"])
                    if upload_exists_queue.mutex:
                        upload_exists_queue.queue.clear()
                    else:
                        try:
                            upload_exists_queue.queue.clear()
                        except Exception as e:
                            print(e)
                #self.console.display("Upload completed")
                self.console.display(["File upload complete of "+self.filename, 'SUCCESS'])
    
    def upload_chunks_main(self, custom_idd = None):

        """is custom_idd is given then it will iterate
         over that idd list and try to upload. if not given then
          it will upload everything from info_dict['file_Serial]"""

        start = timeit.default_timer()       
        dict_info = self.info_dict
        url = self.url+"/upload.php"
        
        threads = list()
        idd_list = list()
        
        if(len(dict_info['file_serial']) < most_working_thread):
            thread_count = len(dict_info['file_serial'])
        else:
            thread_count = most_working_thread
            
        work_count = thread_count
        if custom_idd is not None:
            idd_list = custom_idd 
        else:
            for idd in dict_info['file_serial']:
                idd_list.append(idd) 
        #thr_cou = 0
        #print(idd_list)
        for i in range(thread_count):
            x = threading.Thread(target=self.threading_upload, args=(idd_list[i], url))
            #self.console.display( "thread started: " + str(thr_cou))
            #thr_cou += 1
            x.daemon = True
            threads.append(x)
            x.start()
        #print(threads)
        while len(threads) > 0:
            """continue the loop until all all threads finish working"""
            for thread in threads:
                if not thread.is_alive():
                    threads.pop(threads.index(thread))
                    #print("kaj")
                    if work_count != len(idd_list):
                        x = threading.Thread(target=self.threading_upload,
                         args=(idd_list[work_count], url))
                        #self.console.display( "thread started: " + str(thr_cou))
                        #thr_cou += 1
                        work_count += 1
                        x.daemon = True
                        threads.append(x)
                        x.start()
                   
            
        stop = timeit.default_timer()
        self.console.display( 'Uploading files took '+ str(int(stop - start))+ " seconds.")
        

    def download_chunks(self):

        """main function to download chunks from sever
        all chunks will be downloaded via a different thread.
        this function accepts no extra argument. but info_dict 
        should have all the required value"""

        self.submit_thread_download = threading.Thread(
            target=self.download_chunks_main)
        self.submit_thread_download.daemon = True
        self.submit_thread_download.start()
        self.root.after(500, self.check_thread_download)

    def open_folder_with_file(self):
       
        if os.path.isfile(os.path.join(Path.home(), "Downloads",
                            self.info_dict['dir_to_save_chunk'][0:-32])+ "."+self.info_dict['extension']) is True:
            
            # a hack fix to fetch latest directory data
            # do not use a while loop or any other loop 
            # in tkinter mainloop.

            os.path.getmtime(os.path.join(Path.home(), "Downloads")) 
            if os_platform == 'Windows':
                popen_open = 'explorer /select,"'+os.path.join(Path.home(), "Downloads",self.info_dict['dir_to_save_chunk'][0:-32])+ "."+self.info_dict['extension']+'"'
                subprocess.Popen(popen_open)
            else:
                opener ="open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, os.path.join(Path.home(), "Downloads")])
            #print([popen_open])
        else:
            self.root.after(200, self.open_folder_with_file)
        


    def check_thread_download(self):
        if self.submit_thread_download.is_alive():
            self.root.after(500, self.check_thread_download)
        else:
            #self.console.display("Download completed")
            main_processing_queue.put(self.mergefiles)
            
        #print("cheching thread_downlaod")


    def download_chunks_main(self, custom_idd = None):
        """main function that is called with an individual thread"""
        
        start = timeit.default_timer()       
        
        if(os.path.isdir(os.path.join(Path.home(), "Downloads", "downloads_data",
         self.info_dict['dir_to_save_chunk'])) is False): 
            #checking if the directory exists to downlaod the file. if doesnt then make one
            os.mkdir(os.path.join(Path.home(), "Downloads","downloads_data", self.info_dict['dir_to_save_chunk']))

        # threds will hold all the threads that 
        # will be created to download files
        threads = list()
        idd_list = list()
        

        if(len(self.info_dict['file_serial']) < most_working_thread):
            thread_count = len(self.info_dict['file_serial'])
        else:
            thread_count = most_working_thread

        work_count = thread_count
        #print("work_count: ", work_count)
        if custom_idd is None:
            for idd in range(len(self.info_dict['file_serial'])):
                idd_list.append(idd) 
        else:
            idd_list = custom_idd
        
        #thr_cou = 0

        # iniliazing with firsts threads
        for i in range(thread_count):
            x = threading.Thread(target=self.download_chunk_thread, args=(idd_list[i], ))
            x.daemon = True
            threads.append(x)
            x.start()
        
        # run till all the download is done
        while len(threads) > 0:
            # it will iterate over the threads list
            # and check if the threads is alive
            # if its not then it will create another 
            # thread if there is any download left
            for thread in threads:
                
                if not thread.is_alive():
                    threads.pop(threads.index(thread))
                    if work_count != len(idd_list):
                        x = threading.Thread(target=self.download_chunk_thread, args=(idd_list[work_count], ))                      
                        work_count += 1
                        x.daemon = True
                        threads.append(x)
                        x.start()

                time.sleep(0.2)
                        
        stop = timeit.default_timer()
        self.console.display( 'Downloading Files took '+ str(int(stop - start))+' seconds')
        

    def check_missing_chunk_thread(self):
        if self.missing_chunk_thread.is_alive():
            self.root.after(500, self.check_missing_chunk_thread)    
        else:
            main_processing_queue.put(self.mergefiles)


    def missing_chunks_download(self):
        temp_idd_list = list()
        while download_chunk_queue.empty() != True:
            temp_idd_list.append(download_chunk_queue.get())
        
        if download_chunk_queue.mutex:
            download_chunk_queue.queue.clear()
        else:
            try:
                download_chunk_queue.queue.clear()
            except Exception as e:
                print(e)

        self.missing_chunk_thread = threading.Thread(target=self.download_chunks_main ,
                                            kwargs={'custom_idd': temp_idd_list})
        self.missing_chunk_thread.daemon = True
        self.missing_chunk_thread.start()
        self.root.after(500, self.check_missing_chunk_thread)    

    def download_chunk_thread(self, idd):
        """this is main function that downloads
         a single chunks from server provided with idd(the serial number of chunk"""
        
        down_file = os.path.join(Path.home(), "Downloads", "downloads_data",self.info_dict['dir_to_save_chunk'],
                                 self.info_dict['file_serial'][str(idd)])   
        
        proceed = False
        if os.path.isfile(down_file) is True:
            if not int(idd) == (int(self.info_dict['chunk_count']) - 1):
                if not os.path.getsize(down_file) == 5*mb:
                    proceed = True
        temp_missing_check = True
        if((os.path.isfile(down_file) is False) or proceed):
            
            #try. there can be a connection error due
            #to no internet or no server connection
            
            try:
                #this code 

                chunk_verify = requests.post(self.url+"/download_chunk.php",
                                            data = {'security_key': security_key,
                                                    'data_key' : self.info_dict['dir_to_save_chunk'],
                                                    'file_name' : self.info_dict['file_serial'][str(idd)]},
                                                    headers = {'User-Agent' : user_agent})
                
                if len(chunk_verify.content) > 0: 
                    #server should reply with 'True' if chunk 
                    # exists. so len of chunk_verify.content 
                    # has to be greater than 0
                    
                    print("chunk verify content: ", chunk_verify.content)
                    if (chunk_verify.text == 'True' and chunk_verify.status_code == 200):    
                        downloaded_chunk =  requests.post(self.url+"/download_chunk.php",
                                        data = {'security_key': security_key,
                                                'return_file':'true',
                                                'data_key' : self.info_dict['dir_to_save_chunk'],
                                                'file_name' : self.info_dict['file_serial'][str(idd)]},
                                                headers = {'User-Agent' : user_agent})
                        open(down_file, 'wb').write(downloaded_chunk.content)
                                
                    else:
                        self.console.display(f"chunk {str(idd)} of {self.info_dict['dir_to_save_chunk']} doesnt exist on server")
                    
                else:
                    # this means there is a chunk missed
                    # it can be dure to the user is still
                    # uploading the chunk. So we have a 
                    # function to check for missing chunks
                    temp_missing_check = False
                    print( f"chunk {str(idd)} of {self.info_dict['dir_to_save_chunk']} returned nothing")
                
            except ConnectionError as e:
                    print(e)
                    temp_missing_check = False
                    print("No internet connection in download chunk thread")
                    self.console.display(["No internet connection, Trying in 5 seconds", "ERROR"])
                    if self.download_chunk_thread_count >= 30:
                        self.download_chunk_thread_count = 0
                        download_button.configure(state = tk.NORMAL)
                        return
                        
                    self.root.after(5000, self.download_chunk_thread, idd)
                    #self.root.update_idletasks()
                    #self.root.update()
            
            except Exception as e:
                # if there is something else other than 
                # connectionerror then print it
                print(e)
                temp_missing_check = False

        else:
            # this means there is already a file named same.
            # so we put its idd to a queue 
            # in order to see how much of the file was previously 
            # downloded
            download_exists_queue.put(str(idd))
               
        if temp_missing_check: 
            #incresing the prgress but if temp_missing_check is true
            self.progress_bar(80, int(self.info_dict['chunk_count']))


class App:
    # thanks to https://github.com/beenje/tkinter-logging-text-widget/blob/master/main.py
    # for the code. helped me a lot
    def __init__(self, root):
        self.root = root
        root.title('Simfy File Share')
        #root.iconbitmap(r"icon-0.xbm")
        img = tk.PhotoImage(file='support_files/icon.png')
        root.tk.call('wm', 'iconphoto', self.root._w, img)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        #creating the panes
        vertical_pane = ttk.PanedWindow(self.root, orient=VERTICAL)
        vertical_pane.grid(row=0, column=0, sticky="nsew")

        horizontal_pane = ttk.PanedWindow(vertical_pane, orient=HORIZONTAL)
        vertical_pane.add(horizontal_pane)

        horizontal_down = ttk.PanedWindow(vertical_pane, orient=HORIZONTAL) #down horizontal pan
        vertical_pane.add(horizontal_down)
        
        #creating the frames
        form_frame = ttk.Labelframe(horizontal_pane, text="Upload Area",borderwidth = 10)
        form_frame.columnconfigure(1, weight=1)
        horizontal_pane.add(form_frame, weight=1)
        third_frame = ttk.Labelframe(horizontal_pane, text="Download Area",borderwidth = 10)
        horizontal_pane.add(third_frame, weight=1)
        console_frame = ttk.Labelframe(horizontal_down, text="File Status",borderwidth = 5)
        horizontal_down.add(console_frame, weight=1)
        
        
        # assigning the frames
        self.console = ConsoleUi(console_frame, self.root)
        self.form = UploadSection(form_frame, self.root, self.console)
        self.third = DownloadSection(third_frame,self.root, self.console)
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