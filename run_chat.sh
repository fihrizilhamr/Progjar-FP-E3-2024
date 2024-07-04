#!/bin/sh

sudo apt update -y
sudo apt install pip
pip install flet
sudo apt install libmpv1 -y
python3 server_thread_chat.py &
python3 chat_flet_group.py

# Open 50001/50002/50003