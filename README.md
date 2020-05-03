# simfy_file_share
<h1>A file sharing software based on http restful api with Tkinter gui</h1>

This code is only tested with Python 3 in windows and debian
based linux distros. 

### Python3 required modules:
1. requests (`pip install requests`)
2. psutil (`pip install psutil`)
3. pyperclip (`pip install pyperclip`)
> replace pip with pip3 in linux

### Steps to run:
1. Clone this repo.
2. check if above mentioned modules are available.
3. open `config.py` to add your server's url in 
    `hard_coded_url`. you also need to add your 
    security key in `security_key`. make sure they
    server's security key and and client security key
    matches.
4. run this in cmd/terminal `python simfy_file_share.py` 
>replace python with python3 in linux

Note that, linux doesnt have native support for pyperclip.
So you hvae to use install another package called "xclip"
in debian based operating system. it can be installed with
`apt-get install xclip`

Python tkinter comes with python for windows. But you have to
install it separately in Linux distros. In debian based distros
it can be done with `apt-get install python3-tk`
