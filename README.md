# SimfyShare Python Client

#### A file sharing software based on http restful api with Tkinter gui

For server setup please visit: https://github.com/AshrafAkon/simfyshare_server
This code is only tested with Python 3 in windows and debian
based linux distros. But there shouldnt be any problem with
other operating systems as long as it supports Python 3.

### Python3 required modules:

1. requests (`pip install requests`)
2. psutil (`pip install psutil`)
3. pyperclip (`pip install pyperclip`)
4. pycryptodome (`pip install pycryptodome`)
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
   > replace python with python3 in linux

Note that, Linux doesnt have native support for pyperclip.
So you have to install another package called "xclip".
In debian based operating system. it can be installed with
`apt-get install xclip`. For other Linux disto use your
native installer to install `xclip`.

Python tkinter comes with Python for windows. But you have to
install it separately in Linux distros. In debian based distros
it can be done with `apt-get install python3-tk`. For other Linux
disto use your native installer to install `python3-tk`.
